import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { test } from 'node:test';
import ts from 'typescript';
function harness(){const timers=new Map(),warnings=[];let next=0;const exports={};const code=ts.transpileModule(readFileSync(new URL('../src/radio-state.ts',import.meta.url),'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,esModuleInterop:true}}).outputText;vm.runInNewContext(code,{exports,require:()=>({logger:{warn:message=>warnings.push(message)}}),setTimeout:(fn,delay)=>{const id=++next;timers.set(id,{fn,delay});return id},clearTimeout:id=>timers.delete(id)});return{state:exports,timers,warnings};}
test('band scalar is accepted and no segment is retained',()=>{const h=harness();h.state.processRadioMessage('stn2/band','40');const state=h.state.getRadioState('stn2');assert.equal(state.band,40);assert(!('segment' in state));assert.equal(h.state.getRadioState('stn1').band,null);});
test('zero means N/A and expiry means missing data',()=>{const h=harness();h.state.processRadioMessage('stn1/band','0');assert.equal(h.state.getRadioState('stn1').band,0);for(const timer of h.timers.values())timer.fn();assert.equal(h.state.getRadioState('stn1').band,null);});
test('legacy upgrade input ignores former segment',()=>{const h=harness();h.state.processRadioMessage('stn1/band','[20,5]');const state=h.state.getRadioState('stn1');assert.equal(state.band,20);assert(!('segment' in state));});
test('invalid band messages do not replace the last valid band',()=>{const h=harness();h.state.processRadioMessage('stn1/band','15');for(const value of ['true','null','"20"','-1','20.5','[]','[20]','[20,0,1]','{}'])h.state.processRadioMessage('stn1/band',value);assert.equal(h.state.getRadioState('stn1').band,15);assert.equal(h.warnings.length,9);});
test('missing frequency does not clear the independently received band',()=>{const h=harness();h.state.processRadioMessage('stn1/band','10');h.state.processRadioMessage('stn1/qrg','0');assert.equal(h.state.getRadioState('stn1').band,10);assert.equal(h.state.getRadioState('stn1').frequencyKhz,null);});
