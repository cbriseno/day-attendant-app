"""Approved v5 behavior against disposable real SQLite stores, without live model calls."""
from datetime import timedelta
import json
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch

from day_attendant import archives
from day_attendant.connected import Connected
from day_attendant.errors import AssistantError
from day_attendant.service import Assistant, upgraded_record
from test_connected import NOW, ReviewFixture
from test_daily_domain import DailyBase


class GroupsV5Tests(DailyBase):
    def task(self, uid):
        return next(t for t in self.board.snapshot()['tasks'] if t['id']==uid)

    def test_membership_unicode_alias_and_activity_survive_undo_restart_and_backup(self):
        uid=self.apply('task_add',{'title':'Grupos 🏠','groups':['Casa','Trabajo','CASA','❤','❤️','🏠casa']})['result']['uuid']
        self.assertEqual(self.task(uid)['groups'],['Casa','Trabajo','❤','🏠casa'])
        number=self.task(uid)['number'];created=self.task(uid)['createdAt']
        self.apply('front_activate',{'uuid':uid})
        self.app.clock=lambda:NOW+timedelta(hours=2)
        self.apply('front_todo',{'uuid':uid})
        self.assertEqual(self.task(uid)['lastActiveAt'],self.task(uid)['createdAt'])
        self.assertIsNone(self.task(uid)['startedAt'])
        self.board.undo(self.board.snapshot()['lastFact']['id'],'undo-pause')
        self.assertIsNotNone(self.task(uid)['startedAt'])
        self.assertEqual((self.task(uid)['number'],self.task(uid)['createdAt']),(number,created))
        other=self.add('Other');self.assertGreater(self.task(other)['number'],number)
        self.board.undo(self.board.snapshot()['lastFact']['id'],'undo-create')
        third=self.add('Never reuse');self.assertGreater(self.task(third)['number'],self.task(other)['number'])
        with tempfile.TemporaryDirectory() as folder:
            backup=archives.snapshot(self.app,Path(folder)/'backups')
            restored=Path(folder)/'restored';archives.restore(backup['path'],restored)
            again=Connected(Assistant(restored),ReviewFixture()).snapshot()
            self.assertEqual({t['id']:t['number'] for t in again['tasks']},{t['id']:t['number'] for t in self.board.snapshot()['tasks']})
            self.assertEqual(next(t for t in again['tasks'] if t['id']==uid)['groups'],self.task(uid)['groups'])

    def test_global_merge_closed_retired_colors_and_single_exact_undo(self):
        ids=[self.apply('task_add',{'title':str(n),'groups':groups})['result']['uuid'] for n,groups in enumerate([['Casa','Trabajo'],['Casa','Hogar'],['Casa'],['Hogar']])]
        self.apply('task_done',{'uuid':ids[1]});self.apply('front_retire',{'uuid':ids[2]})
        self.apply('group_color_update',{'group':'Casa','color':'orange'});self.apply('group_color_update',{'group':'Hogar','color':'teal'})
        before=self.app.tasks.rows();colors=self.board.snapshot()['groupColors']
        p=self.apply('group_rename',{'group':'casa','to':'HOGAR'})
        self.assertEqual(p['result']['to'],'Hogar')
        self.assertEqual([self.task(u)['groups'] for u in ids],[['Hogar','Trabajo'],['Hogar'],['Hogar'],['Hogar']])
        self.assertEqual(self.board.snapshot()['groupColors'],{'hogar':'teal'})
        fact=self.board.snapshot()['lastFact'];self.assertTrue(fact['undoable'])
        self.board.undo(fact['id'],'undo-merge')
        self.assertEqual(self.app.tasks.rows(),before);self.assertEqual(self.board.snapshot()['groupColors'],colors)
        self.assertNotIn(fact['id'],[f['id'] for f in self.board.snapshot()['undoStack']])
        self.apply('group_rename',{'group':'Casa','to':'CASA'})
        self.assertEqual(self.task(ids[0])['groups'],['CASA','Trabajo'])

    def test_merge_undo_conflict_is_checked_before_any_member_changes(self):
        a=self.apply('task_add',{'title':'A','groups':['A']})['result']['uuid']
        b=self.apply('task_add',{'title':'B','groups':['A','B']})['result']['uuid']
        self.apply('group_rename',{'group':'A','to':'B'});fact=self.board.snapshot()['lastFact']['id']
        self.apply('task_update',{'uuid':b,'title':'Changed'})
        before=self.app.tasks.rows()
        with self.assertRaises(AssistantError) as error:self.board.undo(fact,'conflicting-undo')
        self.assertEqual(error.exception.code,'undo_conflict');self.assertEqual(before,self.app.tasks.rows())
        self.assertEqual(self.task(a)['groups'],['B'])

    def test_multigroup_drop_replacement_dedup_is_one_undoable_request(self):
        uid=self.apply('task_add',{'title':'Repeated','groups':['Casa','Trabajo','Otro']})['result']['uuid']
        self.apply('task_update',{'uuid':uid,'groups':['Trabajo','Otro']})
        fact=self.board.snapshot()['lastFact']['id']
        self.board.undo(fact,'undo-drop')
        self.assertEqual(self.task(uid)['groups'],['Casa','Trabajo','Otro'])
        restarted=Connected(Assistant(self.temp.name,clock=lambda:NOW),ReviewFixture())
        self.assertTrue(restarted.snapshot()['undoStack'])
        for value in ('Casa',None,[''],['a\nb'],['a'*121],[7]):
            with self.assertRaises(AssistantError):self.request('task_update',{'uuid':uid,'groups':value})

    def test_interrupted_global_rename_recovers_all_participants_and_can_undo(self):
        a=self.apply('task_add',{'title':'Crash A','groups':['Casa','Trabajo']})['result']['uuid']
        b=self.apply('task_add',{'title':'Crash B','groups':['Casa']})['result']['uuid']
        def crash(point):
            if point=='after_task_0':raise RuntimeError('simulated process loss')
        self.app.fault=crash
        with self.assertRaises(RuntimeError):self.request('group_rename',{'group':'Casa','to':'Hogar'})
        self.assertTrue(self.app.store.unresolved())
        restarted=Connected(Assistant(self.temp.name,clock=lambda:NOW),ReviewFixture());restarted.startup()
        self.assertFalse(restarted.store.unresolved())
        rows={t['id']:t for t in restarted.snapshot()['tasks']}
        self.assertEqual(rows[a]['groups'],['Hogar','Trabajo']);self.assertEqual(rows[b]['groups'],['Hogar'])
        restarted.undo(restarted.snapshot()['lastFact']['id'],'undo-recovered-rename')
        self.assertEqual(next(t for t in restarted.snapshot()['tasks'] if t['id']==a)['groups'],['Casa','Trabajo'])

    def test_cli_find_is_read_only_and_returns_the_aliases_uuid(self):
        from contextlib import redirect_stdout
        import io
        from day_attendant.cli import main
        uid=self.add('CLI lookup');number=self.task(uid)['number'];revision=self.app.store.revision()
        output=io.StringIO()
        with patch('day_attendant.web.client',return_value=self.board.snapshot()) as client,redirect_stdout(output):
            code=main(['--json','--state',self.temp.name,'board','find',str(number)])
        self.assertEqual(code,0);self.assertEqual(json.loads(output.getvalue())['data']['tasks'][0]['id'],uid)
        self.assertEqual(self.app.store.revision(),revision);self.assertEqual(client.call_count,1)

    def test_legacy_emoji_color_keys_are_preserved_and_ambiguous_keys_refused(self):
        self.apply('task_add',{'title':'Emoji color','groups':['❤']})
        with self.app.store.connect() as con:con.execute("INSERT OR REPLACE INTO state VALUES('group_colors',?)",(json.dumps({'❤️':'teal'}),))
        self.assertEqual(self.board.snapshot()['groupColors'],{'❤':'teal'})
        self.apply('group_color_update',{'group':'❤','color':'orange'})
        self.board.undo(self.board.snapshot()['lastFact']['id'],'undo-emoji-color')
        self.assertEqual(self.board.snapshot()['groupColors'],{'❤':'teal'})
        with self.app.store.connect() as con:con.execute("INSERT OR REPLACE INTO state VALUES('group_colors',?)",(json.dumps({'❤️':'teal','❤':'orange'}),))
        with self.assertRaises(AssistantError) as error:self.board.snapshot()
        self.assertEqual(error.exception.code,'group_color_conflict')

    def test_chat_resolves_permanent_number_to_uuid_without_model_tools(self):
        from day_attendant.conversation import Conversation,FIELDS
        from test_conversation import ChatFixture
        uid=self.add('Referencia numérica');number=self.task(uid)['number']
        text=f'Pospón la {number} hasta mañana.'
        intent={k:None for k in FIELDS}
        intent.update(action='task_snooze',taskId=str(number),until=(NOW+timedelta(days=1)).isoformat(),clearDue=False,userAuthorized=True,requestEvidence=text)
        self.board.bridge=ChatFixture({'message':'Pospuesta.','uncertainties':[],'intent':intent})
        chat=Conversation(self.board);chat.submit(text,'numeric-chat');chat.run('numeric-chat')
        self.assertEqual(self.task(uid)['state'],'snoozed')
        proposal=next(p for p in self.board.snapshot()['proposals'] if p.get('message_key')=='numeric-chat')
        self.assertEqual(proposal['intent']['payload']['uuid'],uid)


class V5UpgradeTests(DailyBase):
    def setUp(self):
        super().setUp();self.out=tempfile.TemporaryDirectory();self.addCleanup(self.out.cleanup)
        with self.app.store.connect() as con:con.execute("INSERT OR REPLACE INTO state VALUES('backup_directory',?)",(json.dumps(str(Path(self.out.name)/'backups')),))
        self.uid=self.apply('task_add',{'title':'Old','group':'Casa'})['result']['uuid']
        self.apply('task_update',{'uuid':self.uid,'title':'Old edited'})
        # Construct a historical schema-2 fixture; only disposable storage is edited.
        with sqlite3.connect(self.app.tasks.database) as con:
            row=json.loads(con.execute('SELECT data FROM tasks WHERE uuid=?',(self.uid,)).fetchone()[0]);row['project']='Casa';row.pop('groupChanged',None)
            con.execute('UPDATE tasks SET data=? WHERE uuid=?',(json.dumps(row),self.uid));con.execute('DROP TABLE aliases');con.execute('PRAGMA user_version=2')
        self.app.tasks.decoded.clear()
        # Match the old fact's actual record shape for Undo after upgrading.
        with self.app.store.connect() as con:
            fact=con.execute('SELECT id,plan FROM facts ORDER BY id DESC LIMIT 1').fetchone();self.fact=fact['id'];plan=json.loads(fact['plan'])
            for step in plan['steps']:
                for key in ('before','after'):
                    step[key]['project']='Casa';step[key].pop('groupChanged',None)
            con.execute('UPDATE facts SET plan=? WHERE id=?',(json.dumps(plan),self.fact))

    def test_verified_upgrade_idempotent_restore_legacy_archive_and_old_undo(self):
        before=self.app.tasks.rows();revision=self.app.store.revision()
        receipt=archives.upgrade_tasks(self.app)
        self.assertEqual(self.app.tasks.schema(),3)
        self.assertEqual(self.app.tasks.rows(),[upgraded_record(r) for r in before])
        self.assertEqual(self.app.store.revision(),revision);number=self.board.snapshot()['tasks'][0]['number']
        self.assertIsNone(archives.upgrade_tasks(self.app));self.assertEqual(self.app.tasks.aliases()[self.uid],number)
        archives.verify(receipt['backup']['path'])
        target=Path(self.out.name)/'rollback-new';archives.restore(receipt['backup']['path'],target)
        restored=Assistant(target);self.assertEqual(restored.tasks.schema(),3);self.assertEqual(restored.tasks.rows(),self.app.tasks.rows())
        self.board.undo(self.fact,'historical-undo');self.assertEqual(self.app.tasks.get(self.uid)['description'],'Old')

    def test_failed_backup_leaves_old_bytes_and_schema_and_no_alias(self):
        before=self.app.tasks.rows()
        with patch.object(archives,'snapshot',side_effect=AssistantError('backup_space','no space')):
            with self.assertRaises(AssistantError):archives.upgrade_tasks(self.app)
        self.assertEqual(self.app.tasks.schema(),2);self.assertEqual(self.app.tasks.rows(),before);self.assertEqual(self.app.tasks.aliases(),{})

    def test_sql_failure_mid_upgrade_rolls_back_and_retry_succeeds(self):
        before=self.app.tasks.rows()
        with sqlite3.connect(self.app.tasks.database) as con:
            con.execute("CREATE TRIGGER fail_upgrade BEFORE UPDATE ON tasks BEGIN SELECT RAISE(ABORT,'injected'); END")
        with self.assertRaises(AssistantError):archives.upgrade_tasks(self.app)
        self.assertEqual(self.app.tasks.schema(),2);self.assertEqual(self.app.tasks.rows(),before)
        with sqlite3.connect(self.app.tasks.database) as con:con.execute('DROP TRIGGER fail_upgrade')
        archives.upgrade_tasks(self.app);self.assertEqual(self.app.tasks.schema(),3)

    def test_mixed_date_formats_and_unknown_entry_keep_dates_and_get_deterministic_aliases(self):
        from uuid import uuid4
        unknown,earlier=str(uuid4()),str(uuid4())
        self.app.tasks.create({'uuid':unknown,'description':'Unknown creation','entry':None})
        self.app.tasks.create({'uuid':earlier,'description':'Earlier ISO creation','entry':'2020-01-01T12:00:00Z'})
        before=self.app.tasks.rows();archives.upgrade_tasks(self.app)
        self.assertEqual(self.app.tasks.rows(),[upgraded_record(r) for r in before])
        self.assertEqual(self.app.tasks.aliases()[unknown],1)
        self.assertEqual(self.app.tasks.aliases()[earlier],2)
        self.assertIsNone(self.app.tasks.get(unknown)['entry'])

    def test_invalid_legacy_conversion_rolls_back_all_rows_and_registry(self):
        from uuid import uuid4
        uid=str(uuid4());self.app.tasks.create({'uuid':uid,'description':'Legacy long group','project':'x'*121})
        before=self.app.tasks.rows()
        with self.assertRaises(AssistantError):archives.upgrade_tasks(self.app)
        self.assertEqual(self.app.tasks.schema(),2);self.assertEqual(self.app.tasks.rows(),before)
        with self.app.tasks.connect() as con:self.assertIsNone(con.execute("SELECT 1 FROM sqlite_master WHERE name='aliases'").fetchone())
