import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import vm from 'node:vm';
const fixture=JSON.parse(execFileSync('python3',['-c',`
import sys,json
from pathlib import Path
sys.path.insert(0,'svc/control')
from config_layout import compose
from types import SimpleNamespace
from controller import Controller
p=Path('cfg/control');a,b,c=compose(json.loads((p/'installation.example.json').read_text()),json.loads((p/'initial-state.example.json').read_text()))
m=[];e=Controller(SimpleNamespace(stn1=a['stn1'],stn2=a['stn2'],stacks=b,sixpack=c),lambda t,p:m.append([t,p]));e.reconnect()
for topic in e.feedback:e.handle(topic,'OFF')
e.handle('stn1/tx','0');e.handle('stn2/tx','0');e.handle('stn2/band','20');e.tick()
print(json.dumps({'messages':m,'snapshot':json.loads(e.last_snapshot)}))
`],{cwd:new URL('../../../',import.meta.url),encoding:'utf8'}));
const packets=Object.fromEntries(fixture.messages.filter(([t])=>['control/config','pytofront','control/heartbeat'].includes(t)));
function harness(){let now=0,id=0;const timers=new Map(),states=[],freshness=[],module={exports:{}};vm.runInNewContext(readFileSync(new URL('../../../static/control-state.js',import.meta.url),'utf8'),{module});const feed=module.exports.createConsumer(s=>states.push(JSON.parse(JSON.stringify(s))),f=>freshness.push(f),{now:()=>now,setTimeout:fn=>{timers.set(++id,fn);return id},clearTimeout:i=>timers.delete(i)});return{feed,states,freshness,send:(t,p=packets[t])=>feed.receive(t,p),expire:()=>{now+=5001;for(const fn of [...timers.values()])fn()}};}
function all(h){for(const t of ['control/config','pytofront','control/heartbeat'])h.send(t);}
test('shared decoder reconstructs all consumed fields from the actual Python publisher',()=>{const h=harness();all(h);assert.equal(h.feed.isFresh(),true);const state=h.states.at(-1),old=fixture.snapshot;for(const s of ['stn1','stn2'])for(const key of ['netbios','auto','band','rig','confirmed_band','relay_status','conflict'])assert.equal(state[s][key],old[s][key],s+'.'+key);for(const [band,stack]of Object.entries(old.stacks)){assert.equal(state.stacks[band].salidas,stack.salidas);for(let i=1;i<=stack.salidas;i++)for(const key of ['nombre','tw','haz','estado'])assert.equal(state.stacks[band][i][key],stack[i][key],band+'.'+i+'.'+key);for(let i=1;i<=3;i++)assert.ok(state.stacks[band][i]);}});
test('all arrival orders work; retained catalog/state alone are never live',()=>{const topics=['control/config','pytofront','control/heartbeat'];for(const order of [[0,1,2],[0,2,1],[1,0,2],[1,2,0],[2,0,1],[2,1,0]]){const h=harness();for(const i of order)h.send(topics[i]);assert.equal(h.feed.isFresh(),true);assert.equal(h.states.length,1);}const h=harness();h.send('control/config');h.send('pytofront');assert.equal(h.feed.isFresh(),false);assert.equal(h.states.length,0);});
test('heartbeat renews freshness without rendering; expiry and recovery work',()=>{const h=harness();all(h);for(let i=0;i<4;i++)h.send('control/heartbeat');assert.equal(h.states.length,1);h.expire();assert.equal(h.feed.isFresh(),false);h.send('control/heartbeat');assert.equal(h.feed.isFresh(),true);assert.equal(h.states.length,2);});
test('offline and new session invalidate stored state until matching heartbeat/state',()=>{const h=harness();all(h);h.feed.receive('control/availability','offline');assert.equal(h.feed.isFresh(),false);h.send('pytofront');assert.equal(h.feed.isFresh(),false);h.send('control/heartbeat');assert.equal(h.feed.isFresh(),true);h.send('control/heartbeat',JSON.stringify({s:'new',r:1}));assert.equal(h.feed.isFresh(),false);const next=JSON.parse(packets.pytofront);next.s='new';h.send('pytofront',JSON.stringify(next));assert.equal(h.feed.isFresh(),true);});
test('wrong catalog, missed revision and malformed input cannot refresh data',()=>{const h=harness();all(h);const next=JSON.parse(packets.pytofront);next.c='other';h.send('pytofront',JSON.stringify(next));assert.equal(h.feed.isFresh(),false);h.send('pytofront');const hb=JSON.parse(packets['control/heartbeat']);hb.r++;h.send('control/heartbeat',JSON.stringify(hb));assert.equal(h.feed.isFresh(),false);h.send('control/heartbeat','bad');assert.equal(h.feed.isFresh(),false);});
test('unknown antenna remains unconfirmed',()=>{const h=harness(),next=JSON.parse(packets.pytofront);next.stacks['20'][0]=null;h.send('control/config');h.send('pytofront',JSON.stringify(next));h.send('control/heartbeat');assert.equal(h.states[0].stacks['20']['1'].confirmed,false);});
test('legacy snapshots support installing new consumers before control',()=>{const h=harness();h.send('pytofront',JSON.stringify(fixture.snapshot));assert.equal(h.feed.isFresh(),true);h.expire();assert.equal(h.feed.isFresh(),false);});
test('every web consumer and Stream Deck load the shared decoder',()=>{const folder=new URL('../../../static/',import.meta.url);for(const file of readdirSync(folder).filter(f=>f.endsWith('.html'))){const html=readFileSync(new URL(file,folder),'utf8');if(!html.includes('mqtt.js')&&!html.includes('class TinyMqtt'))continue;assert.ok(html.includes('control-state.js'),file);assert.ok(html.indexOf('control-state.js')<(html.includes('class TinyMqtt')?html.indexOf('class TinyMqtt'):html.indexOf('src="mqtt.js"')),file);}const plugin=readFileSync(new URL('../src/mqtt.ts',import.meta.url),'utf8');assert.ok(plugin.includes('../../../static/control-state.js'));assert.ok(plugin.includes('controlFeed.receive(topic, value)'));});
