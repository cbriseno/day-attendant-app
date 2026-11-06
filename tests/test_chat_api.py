"""App operations use the real isolated HTTP API with both controlled native adapters."""
import base64
import json
import threading
import unittest

from day_attendant.api_contract import OPERATIONS
from day_attendant.conversation import FIELDS
from day_attendant.web import LocalServer
from test_chat_contract import controlled_board


class ChatApi(unittest.TestCase):
    def test_local_api_results_maintenance_and_existing_confirmations(self):
        for provider in ('codex','claude'):
            with self.subTest(provider=provider),controlled_board(provider) as (board,folder):
                server=LocalServer(board.app,board.bridge);server.schedule=lambda result=None:None
                server.catalogs={'codex':[],'claude':[]}
                thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
                count=0
                def invoke(action,args,ok=True):
                    nonlocal count
                    count+=1;text='Apply the requested '+action;key='api-'+str(count)
                    intent=dict.fromkeys(FIELDS);intent.update(action=action,operationPayload=args,clearDue=False,userAuthorized=True,requestEvidence=text)
                    (folder/'output.json').write_text(json.dumps({'message':'The service will validate the request.','uncertainties':[],'intent':intent,'additionalIntents':[],'unprocessed':[]}))
                    server.chat.submit(text,key);server.chat.run(key)
                    reply=next(m for m in board.snapshot()['messages'] if m['key']==key+':assistant')
                    self.assertEqual(reply['status'],'completed',reply)
                    outcome=json.loads(reply['data'])['operation_results'][0]
                    self.assertEqual(outcome['ok'],ok,outcome)
                    return outcome.get('result')
                try:
                    uid=board.request('task_add',{'title':'Synthetic task'},'seed')['result']['uuid']
                    fact=board.snapshot()['lastFact']['id']
                    invoke('profile_configure',{'values':{'locale':'es','notification_policy':{'dailyBudget':4}}})
                    self.assertEqual(board.snapshot()['notification_policy']['start'],'09:00')
                    invoke('checkins_settings',{'values':{'enabled':False,'kinds':{'risk':False}}})
                    for name,args in [('doctor',{}),('zone_rules',{'year':2026}),('model_list',{}),('diagnostics_preview',{}),('diagnostics_export',{}),('backup_create',{}),('backup_list',{})]:
                        invoke(name,args)
                    self.assertTrue(board.store.state_value('last_backup'))
                    self.assertTrue(str(board.store.state_value('last_backup')['path']).startswith(str(folder)))
                    attachment=invoke('attachment_upload',{'name':'synthetic.txt','mime':'text/plain','base64':base64.b64encode(b'Synthetic selected content').decode(),'purpose':'task'})
                    self.assertGreater(invoke('attachment_read',{'id':attachment['id']})['bytes'],0)
                    invoke('undo_fact',{'fact_id':fact})
                    self.assertEqual(next(t for t in board.snapshot()['tasks'] if t['id']==uid)['state'],'retired')
                    board.request('task_reopen',{'uuid':uid},'reopen')
                    retire=board.request('front_retire',{'uuid':uid},'retire',origin='chat')
                    invoke('proposal_confirm',{'id':retire['id'],'generation':retire['generation']})
                    board.request('task_reopen',{'uuid':uid},'reopen-again')
                    retire=board.request('front_retire',{'uuid':uid},'retire-again',origin='chat')
                    invoke('proposal_retry',{'id':retire['id']})
                    invoke('proposal_cancel',{'id':retire['id']})
                    invoke('undo_proposals',{'proposal_ids':[board.request('task_update',{'uuid':uid,'priority':'high'},'priority')['id']]})
                    raw=board.request('task_add',{'title':'Synthetic raw'},'raw')['result']['uuid']
                    board.request('organize_capture',{'uuid':raw,'expectedTitle':'Synthetic raw','original':'Synthetic raw','tasks':[{'title':'Synthetic organized','notes':'Synthetic','groups':[],'after':[]}]},'organize')
                    invoke('undo_organization',{'fact_id':board.snapshot()['lastFact']['id']})
                    invoke('recovery_inspect',{'operation_key':'synthetic-missing'},ok=False)
                    invoke('recovery_resolve',{'operation_key':'synthetic-missing','resolution':'keep_observed','precondition':'synthetic'},ok=False)
                    invoke('suggestion_accept',{'id':'00000000-0000-4000-8000-000000000000'},ok=False)
                    invoke('suggestion_dismiss',{'id':'00000000-0000-4000-8000-000000000000'},ok=False)
                    invoke('assistant_mode',{'mode':'off'})
                    self.assertEqual(board.snapshot()['agentMode']['mode'],'off')
                finally:
                    server.shutdown();thread.join(5);server.server_close();server.pool.shutdown(wait=True)
                self.assertFalse(thread.is_alive())

    def test_every_registered_app_operation_has_a_typed_fixed_local_route(self):
        for name,(method,route,description,fields) in OPERATIONS.items():
            self.assertIn(method,('GET','POST'));self.assertTrue(route.startswith('/api/'))
            self.assertNotIn('://',route);self.assertTrue(description)
            self.assertTrue(all(isinstance(schema,dict) for schema in fields.values()),name)
