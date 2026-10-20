// Synthetic arithmetic only. No data retrieval, portfolio engine or trading.
import assert from 'node:assert/strict';
const finite = (...xs) => { if (!xs.every(x => typeof x === 'number' && Number.isFinite(x))) throw new Error('Numeric finite inputs required; missing is never zero'); };
export function ev(up, loss, p, cost) {
  finite(up, loss, p, cost);
  if (up < 0 || loss < 0 || loss > 1 || p < 0 || p > 1 || cost < 0) throw new Error('Invalid scenario');
  return p * up - (1-p) * loss - cost; // net profit / initial asset notional
}
export function breakEven(up, loss, cost, hurdle=0) {
  finite(up, loss, cost, hurdle);
  ev(up, loss, .5, cost);
  if (up+loss <= 0 || hurdle < 0) throw new Error('Invalid payoff or hurdle');
  return (loss+cost+hurdle)/(up+loss); // may exceed 1: infeasible, do not clip
}
export function annualized(up, days) {
  finite(up, days);
  if (days <= 0 || up <= -1) throw new Error('Invalid duration or return');
  return (1+up)**(365/days)-1;
}
function selfTest() {
  assert.ok(Math.abs(ev(.05,.4,.9,.01)-(-.005)) < 1e-12);
  assert.ok(Math.abs(ev(.05,.4,.95,.01)-.0175) < 1e-12);
  assert.ok(Math.abs(breakEven(.05,.4,.01)-41/45) < 1e-12);
  const p = breakEven(.05,.4,.01);
  assert.ok(Math.abs(ev(.05,.4,p,.01)) < 1e-12);
  assert.ok(breakEven(.01,.4,.02) > 1);
  assert.ok(annualized(.05,90) > annualized(.05,270));
  assert.ok(breakEven(.05,.4,.02) > breakEven(.05,.4,.01));
  assert.throws(()=>ev(.05,.4,null,.01));
  assert.throws(()=>ev(.05,.4,NaN,.01));
  assert.throws(()=>ev(.05,.4,1.1,.01));
  assert.throws(()=>annualized(.05,0));
  assert.equal(ev(.05,1,0,.01),-1.01);
  console.log('PASS: 12 synthetic checks; no empirical edge tested.');
}
if (process.argv.includes('--self-test')) selfTest();
else {
  console.log('kind,upside,loss_if_failed,cost,p_assumed,days,metric,value');
  for (const up of [.02,.05,.10]) for (const loss of [.10,.20,.40,.60,1]) for(const cost of [.0025,.005,.01,.02]) {
    console.log(['SYNTHETIC',up,loss,cost,'NA','NA','break_even_probability',breakEven(up,loss,cost).toFixed(10)].join(','));
  }
  for (const p of [.90,.95,.99]) console.log(['SYNTHETIC',.05,.4,.01,p,'NA','expected_profit_per_notional',ev(.05,.4,p,.01).toFixed(10)].join(','));
  for (const days of [90,180,270,455]) console.log(['SYNTHETIC',.05,'NA',0,1,days,'annualized_success_only',annualized(.05,days).toFixed(10)].join(','));
  for (const days of [90,270,455]) {
    const hurdle=(1.02)**(days/365)-1; // assumed cash rate, not observed benchmark
    console.log(['SYNTHETIC',.05,.4,.01,'NA',days,'break_even_with_2pct_annual_cash',breakEven(.05,.4,.01,hurdle).toFixed(10)].join(','));
  }
}
