"""Frozen paired-grid gates, shared by capture and independent calibration audit."""
import math
from feeds import clock_quality


def reasons(grid):
    tick = grid['grid_ms']; errors = []
    if not 0 <= grid['captured_ms']-tick <= 250:
        errors.append('GRID_LATENESS')
    if grid['clock_step']:
        errors.append('WALL_CLOCK_STEP')
    obs = grid['observations']
    if grid.get('outcomes_opened') != 0 or grid.get('signals_emitted') != 0:
        errors.append('SETUP_OUTCOME_LOCK')
    for venue in ['binance', 'mexc']:
        book = obs.get(venue, {})
        if not all(k in book for k in ['exchange_ms', 'received_ms', 'bid', 'ask', 'mid', 'sequence']):
            errors.append(venue.upper()+'_NO_BOOK'); continue
        if not 0 <= tick-book['received_ms'] <= 1000:
            errors.append(venue.upper()+'_RECEIPT_AGE')
        if not -250 <= tick-book['exchange_ms'] <= 1000:
            errors.append(venue.upper()+'_EXCHANGE_AGE')
        if not all(isinstance(book[k], (int, float)) and math.isfinite(book[k]) for k in ['bid', 'ask', 'mid']) or not 0 < book['bid'] < book['ask'] or not math.isclose(book['mid'], (book['bid']+book['ask'])/2, rel_tol=1e-12):
            errors.append(venue.upper()+'_INVALID_BOOK')
        for field, age in [('clocks', 120000), ('metadata', 3600000)]:
            proof = grid[field].get(venue, {})
            qualified = proof.get('valid') is True
            if field == 'clocks':
                qualified = qualified and clock_quality(proof, proof)
            if not qualified or not 0 <= tick-proof.get('received_ms', tick+1) <= age:
                errors.append(venue.upper()+'_'+field.upper())
    if all('exchange_ms' in obs.get(v, {}) for v in ['binance', 'mexc']):
        if abs(obs['binance']['exchange_ms']-obs['mexc']['exchange_ms']) > 500:
            errors.append('CROSSVENUE_TIMESTAMP_DIFFERENCE')
    return errors
