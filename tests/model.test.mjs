import test from 'node:test';
import assert from 'node:assert/strict';
import { periods } from '../web/model.mjs';
test('construction year is excluded and zero stays distinct from an empty period',()=>{
  assert.deepEqual(periods([2022,2023,2024],[[0,0],[8,1],[6,4]],2023,1),[{years:1,mean:0},{years:1,mean:4}]);
  assert.equal(periods([2024],[[5,1]],2024,0)[0].mean,null);
});
