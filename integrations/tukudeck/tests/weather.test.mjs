import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import vm from 'node:vm';
import { test } from 'node:test';
import ts from 'typescript';

const root=new URL('../',import.meta.url);
function harness(){
  let now=Date.parse('2026-10-11T18:33:00Z'),nextTimer=0;
  class Clock extends Date{static now(){return now}}
  const timers=new Map(),images=[];
  function load(path,requires={}){
    const source=readFileSync(new URL(path,root),'utf8');
    const code=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,experimentalDecorators:true}}).outputText;
    const exports={};
    vm.runInNewContext(code,{exports,require:name=>{assert(name in requires,`Unexpected import ${name}`);return requires[name]},Date:Clock,
      setInterval:(fn,ms)=>{const id=++nextTimer;timers.set(id,{fn,ms});return id},clearInterval:id=>timers.delete(id)});
    return exports;
  }
  const state=load('src/weather-state.ts');
  const {Weather}=load('src/actions/weather.ts',{
    '@elgato/streamdeck':{SingletonAction:class{},action:()=>Class=>Class},
    '../key-display':{setKeyImage:(action,image)=>{images.push({id:action.id,svg:decodeURIComponent(image.split(',').slice(1).join(','))});return Promise.resolve()}},
    '../weather-state':state
  });
  const weather=new Weather();
  const event=(id,settings={})=>({action:{id,setImage:async()=>{}},payload:{settings}});
  const packet=(fields,age=0)=>state.processWeatherMessage(JSON.stringify({received_at:new Clock(now-age).toISOString(),fields}));
  const advance=ms=>{now+=ms;for(const {fn} of [...timers.values()])fn()};
  return {state,weather,event,packet,advance,timers,images,now:()=>now};
}

test('settings: defaults, order, deduplication and interval limits',()=>{
  const {state}=harness();
  assert.equal(state.selectedWeatherMetrics({}).length,5);
  assert.equal(JSON.stringify(state.selectedWeatherMetrics({metrics:['daily_rain_mm','bad','temp_out_c','daily_rain_mm']})),JSON.stringify(['daily_rain_mm','temp_out_c']));
  assert.equal(state.selectedWeatherMetrics({metrics:[]}).length,0);
  assert.equal(state.weatherInterval({}),5000);
  assert.equal(state.weatherInterval({interval:0}),1000);
  assert.equal(state.weatherInterval({interval:100}),60000);
  assert.equal(state.weatherInterval({interval:'bad'}),5000);
});
test('retained data: values, zero, missing fields and stale/future dates',()=>{
  const h=harness();h.packet({temp_out_c:15.722,wind_speed_kmh:0,wind_dir_deg:277});
  assert.equal(h.state.formatWeatherMetric('temp_out_c',h.state.getWeatherState()).value,'15,7');
  assert.equal(h.state.formatWeatherMetric('wind_speed_kmh',h.state.getWeatherState()).value,'0,0');
  assert.equal(h.state.formatWeatherMetric('wind_dir_deg',h.state.getWeatherState()).unit,'O');
  assert.equal(h.state.formatWeatherMetric('daily_rain_mm',h.state.getWeatherState()).value,'--');
  h.advance(300001);assert.equal(h.state.getWeatherState().stale,true);
  h.packet({temp_out_c:12},-120000);assert.equal(h.state.getWeatherState().stale,true);
  h.state.processWeatherMessage('invalid');assert.equal(h.state.getWeatherState().stale,true);
  h.packet({temp_out_c:null,humidity_out_pct:94});assert.equal(h.state.getWeatherState().fields.temp_out_c,undefined);
  assert.equal(h.state.getWeatherState().fields.humidity_out_pct,94);
});
test('automatic rotation, button advances, and press resets the interval',()=>{
  const h=harness();h.packet({temp_out_c:15.7,humidity_out_pct:94,wind_speed_kmh:0});
  h.weather.onWillAppear(h.event('a',{metrics:['temp_out_c','humidity_out_pct','wind_speed_kmh'],interval:5}));
  assert.match(h.images.at(-1).svg,/TEMP\. EXTERIOR/);
  h.advance(5000);assert.match(h.images.at(-1).svg,/HUMEDAD/);
  h.weather.onKeyDown(h.event('a'));assert.match(h.images.at(-1).svg,/VIENTO/);
  const count=h.images.length;h.advance(4000);assert.equal(h.images.length,count);
  h.advance(1000);assert.match(h.images.at(-1).svg,/TEMP\. EXTERIOR/);
});
test('hidden keys dispose listeners and timers; reconfiguration replaces them',()=>{
  const h=harness();h.weather.onWillAppear(h.event('a'));assert.equal(h.timers.size,1);
  h.weather.onDidReceiveSettings(h.event('a',{metrics:['daily_rain_mm'],interval:2}));assert.equal(h.timers.size,1);
  const count=h.images.length;h.advance(10000);assert.equal(h.images.length,count);
  h.weather.onWillDisappear(h.event('a'));assert.equal(h.timers.size,0);
  h.packet({daily_rain_mm:12});assert.equal(h.images.length,count);
  h.weather.onDidReceiveSettings(h.event('a'));assert.equal(h.timers.size,0);
});
test('visible fixed metric expires without further messages',()=>{
  const h=harness();h.packet({temp_out_c:15.7});h.weather.onWillAppear(h.event('a',{metrics:['temp_out_c']}));
  assert.match(h.images.at(-1).svg,/15,7/);h.advance(300001);
  assert.match(h.images.at(-1).svg,/>--</);assert.match(h.images.at(-1).svg,/#808080/);
});
test('multiple keys rotate independently; empty selection is handled',()=>{
  const h=harness();h.weather.onWillAppear(h.event('a',{metrics:['temp_out_c','humidity_out_pct'],interval:2}));
  h.weather.onWillAppear(h.event('b',{metrics:['daily_rain_mm','rain_rate_mm_h'],interval:5}));
  h.advance(2000);assert.match(h.images.filter(x=>x.id==='a').at(-1).svg,/HUMEDAD/);
  assert.match(h.images.filter(x=>x.id==='b').at(-1).svg,/LLUVIA HOY/);
  h.weather.onWillAppear(h.event('c',{metrics:[]}));assert.match(h.images.at(-1).svg,/SIN SELECCIÓN/);
  const count=h.images.length;h.weather.onKeyDown(h.event('c'));assert.equal(h.images.length,count);
});
test('manifest action, property inspector and registration agree',()=>{
  const manifest=JSON.parse(readFileSync(new URL('com.eb1tr.tukudeck.sdPlugin/manifest.json',root),'utf8'));
  const action=manifest.Actions.find(a=>a.UUID==='com.eb1tr.tukudeck.weather');assert(action);
  const inspector=new URL('com.eb1tr.tukudeck.sdPlugin/'+action.PropertyInspectorPath,root);assert(existsSync(inspector));
  const html=readFileSync(inspector,'utf8');new vm.Script(html.match(/<script>([\s\S]*?)<\/script>/)[1]);
  assert.match(readFileSync(new URL('src/plugin.ts',root),'utf8'),/registerAction\(new Weather\(\)\)/);
  assert.match(readFileSync(new URL('src/mqtt.ts',root),'utf8'),/processWeatherMessage\(value\)/);
});

test('inspector preserves unchecked values and row order across delayed echoes and reopen',()=>{
  class Element {
    children=[];listeners={};value='';checked=false;
    append(...children){this.children.push(...children)}
    replaceChildren(...children){this.children=children}
    addEventListener(event,listener){this.listeners[event]=listener}
    setAttribute(){}
    checkValidity(){return true}
  }
  const elements=Object.fromEntries(['metrics','interval','color'].map(id=>[id,new Element()]));
  const sockets=[];
  class Socket {
    static OPEN=1;readyState=1;messages=[];
    constructor(){sockets.push(this)}
    send(message){this.messages.push(JSON.parse(message))}
  }
  const document={getElementById:id=>elements[id],createElement:()=>new Element(),createTextNode:text=>({text})};
  const window={},context=vm.createContext({document,window,WebSocket:Socket});
  const html=readFileSync(new URL('com.eb1tr.tukudeck.sdPlugin/ui/weather.html',root),'utf8');
  vm.runInContext(html.match(/<script>([\s\S]*?)<\/script>/)[1],context);
  const open=settings=>window.connectElgatoStreamDeckSocket('1234','inspector','registerPropertyInspector','{}',JSON.stringify({context:'key',action:'com.eb1tr.tukudeck.weather',payload:{settings}}));
  open({});sockets[0].onopen();
  const checkbox=elements.metrics.children[0].children[0].children[0];
  assert.equal(checkbox.checked,true);checkbox.checked=false;checkbox.listeners.change();
  const saved=sockets[0].messages.at(-1);assert.equal(saved.event,'setSettings');
  // Stream Deck requires the registered inspector UUID for PI setSettings,
  // not the action context supplied inside actionInfo.
  assert.equal(saved.context,'inspector');
  assert.equal(saved.action,'com.eb1tr.tukudeck.weather');
  assert.equal(saved.payload.metrics.includes('temp_out_c'),false);
  sockets[0].onmessage({data:JSON.stringify({event:'didReceiveSettings',context:'key',payload:{settings:{}}})});
  assert.equal(elements.metrics.children[0].children[0].children[0],checkbox);
  assert.equal(checkbox.checked,false);
  open(saved.payload);sockets[1].onopen();
  assert.equal(elements.metrics.children[0].children[0].children[0].checked,false);
  assert.equal(elements.metrics.children[0].children[0].children[1].text,'Temperatura exterior');
  const up=elements.metrics.children[1].children[1];up.listeners.click();
  const reordered=sockets[1].messages.at(-1).payload;
  open(reordered);assert.equal(elements.metrics.children[0].children[0].children[1].text,'Humedad exterior');
});
