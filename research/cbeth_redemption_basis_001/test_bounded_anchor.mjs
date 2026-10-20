import {test} from 'node:test';
import assert from 'node:assert/strict';
import {validHeader,validRate} from './bounded_anchor_source.mjs';
test('historical identity rejects latest substitution and malformed provenance',()=>{
 const h={number:'0xf42400',hash:'0x'+'a'.repeat(64),timestamp:'0x123'};
 assert.ok(validHeader(h));assert.ok(!validHeader({...h,number:'latest'}));assert.ok(!validHeader({...h,hash:'0x12'}));assert.ok(!validHeader(null));
});
test('rate must be exact positive ABI uint256, not empty/error/zero',()=>{
 assert.ok(validRate('0x'+'0'.repeat(63)+'1'));for(const v of [undefined,null,'0x','0x01','0x'+'0'.repeat(64),{error:'archive unavailable'}]) assert.ok(!validRate(v));
});
