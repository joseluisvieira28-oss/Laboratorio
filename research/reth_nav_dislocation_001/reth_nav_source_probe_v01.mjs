import { JsonRpcProvider, Contract, getAddress, ZeroAddress } from "ethers";
import fs from "fs";

const RPC = process.env.ETH_RPC_URL || "https://ethereum-rpc.publicnode.com";
const provider = new JsonRpcProvider(RPC);

const RETH = getAddress("0xae78736Cd615f374D3085123A210448E74Fc6393");
const WETH = getAddress("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2");
const FACTORY = getAddress("0x1F98431c8aD98523631AE4a59f267346ea31F984");

const SENTINELS = [18000000, 20000000, 22000000, 24000000];
const FEES = [100, 500, 3000, 10000];

const reth = new Contract(RETH, ["function getExchangeRate() view returns (uint256)"], provider);
const factory = new Contract(FACTORY, ["function getPool(address,address,uint24) view returns (address)"], provider);

async function blockMeta(n) {
  const b = await provider.getBlock(n);
  if (!b) throw new Error("BLOCK_NOT_FOUND_" + n);
  return { number: Number(b.number), hash: b.hash, timestamp: Number(b.timestamp) };
}

async function finalizedMeta() {
  const raw = await provider.send("eth_getBlockByNumber", ["finalized", false]);
  if (!raw) throw new Error("FINALIZED_BLOCK_NOT_FOUND");
  return {
    number: Number(BigInt(raw.number)),
    hash: raw.hash,
    timestamp: Number(BigInt(raw.timestamp))
  };
}

function exactWethPerReth(token0, token1, sqrtPriceX96) {
  const q192 = 1n << 192n;
  const s = BigInt(sqrtPriceX96);
  const ratioNum = s * s;
  if (token0.toLowerCase() === RETH.toLowerCase() && token1.toLowerCase() === WETH.toLowerCase()) {
    return { numerator: ratioNum.toString(), denominator: q192.toString(), orientation: "WETH_PER_RETH" };
  }
  if (token0.toLowerCase() === WETH.toLowerCase() && token1.toLowerCase() === RETH.toLowerCase()) {
    return { numerator: q192.toString(), denominator: ratioNum.toString(), orientation: "WETH_PER_RETH_INVERTED" };
  }
  throw new Error("TOKEN_ORDER_NOT_RETH_WETH");
}

const receipt = {
  lab_id: "RETH-NAV-DISLOCATION-001",
  stage: "SOURCE_GATE_V0.1",
  captured_at_utc: new Date().toISOString(),
  classification: "SOURCE_BLOCKED",
  rpc: RPC,
  canonical_addresses: { reth: RETH, weth: WETH, uniswap_v3_factory: FACTORY },
  fixed_historical_sentinels: SENTINELS,
  fee_tiers_probed: FEES,
  protocol_anchor: [],
  pools: [],
  errors: [],
  market_returns_opened: false,
  direction_opened: false,
  pnl_opened: false,
  mutation: false,
  promotion_credit: 0
};

try {
  const finalized = await finalizedMeta();
  receipt.finalized_block = finalized;
  const blocks = [...SENTINELS, finalized.number];

  for (const n of blocks) {
    try {
      const meta = n === finalized.number ? finalized : await blockMeta(n);
      const rate = await reth.getExchangeRate({ blockTag: n });
      receipt.protocol_anchor.push({
        ...meta,
        getExchangeRate_wei_per_reth: rate.toString(),
        block_pinned: true
      });
    } catch (e) {
      receipt.errors.push({ scope: "protocol_anchor", block: n, error: String(e?.shortMessage || e?.message || e) });
    }
  }

  for (const fee of FEES) {
    let poolAddr;
    try {
      poolAddr = await factory.getPool(RETH, WETH, fee);
    } catch (e) {
      receipt.errors.push({ scope: "factory_getPool", fee, error: String(e?.shortMessage || e?.message || e) });
      continue;
    }
    if (!poolAddr || poolAddr === ZeroAddress) {
      receipt.pools.push({ fee, pool: ZeroAddress, discovered: false, historical_reads: [] });
      continue;
    }

    const pool = new Contract(poolAddr, [
      "function token0() view returns (address)",
      "function token1() view returns (address)",
      "function liquidity() view returns (uint128)",
      "function slot0() view returns (uint160 sqrtPriceX96,int24 tick,uint16 observationIndex,uint16 observationCardinality,uint16 observationCardinalityNext,uint8 feeProtocol,bool unlocked)"
    ], provider);

    const entry = { fee, pool: getAddress(poolAddr), discovered: true, historical_reads: [], errors: [] };
    try {
      entry.token0 = getAddress(await pool.token0());
      entry.token1 = getAddress(await pool.token1());
      entry.current_liquidity = (await pool.liquidity()).toString();
      entry.token_order_verified =
        [entry.token0.toLowerCase(), entry.token1.toLowerCase()].sort().join(":") ===
        [RETH.toLowerCase(), WETH.toLowerCase()].sort().join(":");
    } catch (e) {
      entry.errors.push({ scope: "pool_identity", error: String(e?.shortMessage || e?.message || e) });
    }

    for (const n of blocks) {
      try {
        const meta = n === finalized.number ? finalized : await blockMeta(n);
        const s = await pool.slot0({ blockTag: n });
        const liq = await pool.liquidity({ blockTag: n });
        const exact = exactWethPerReth(entry.token0, entry.token1, s.sqrtPriceX96);
        entry.historical_reads.push({
          ...meta,
          sqrtPriceX96: s.sqrtPriceX96.toString(),
          tick: Number(s.tick),
          liquidity: liq.toString(),
          exact_weth_per_reth: exact,
          block_pinned: true
        });
      } catch (e) {
        entry.errors.push({ scope: "historical_pool_state", block: n, error: String(e?.shortMessage || e?.message || e) });
      }
    }
    receipt.pools.push(entry);
  }

  const anchorBlocks = new Set(receipt.protocol_anchor.map(x => x.number));
  const anchorPass = [...SENTINELS, finalized.number].every(n => anchorBlocks.has(n));
  const usablePools = receipt.pools.filter(p =>
    p.discovered &&
    p.token_order_verified === true &&
    p.historical_reads.filter(x => SENTINELS.includes(x.number)).length >= 3
  );

  receipt.gates = {
    protocol_anchor_all_sentinels_plus_finalized: anchorPass,
    discovered_nonzero_pool_count: receipt.pools.filter(p => p.discovered).length,
    usable_historical_pool_count: usablePools.length,
    silent_latest_fallback: false
  };

  if (anchorPass && usablePools.length >= 1) {
    receipt.classification = "SOURCE_PASS";
  } else {
    receipt.classification = "SOURCE_BLOCKED";
  }
} catch (e) {
  receipt.errors.push({ scope: "fatal", error: String(e?.shortMessage || e?.message || e) });
  receipt.classification = "SOURCE_BLOCKED";
}

fs.mkdirSync("artifacts", { recursive: true });
fs.writeFileSync("artifacts/reth_nav_source_gate_v01.json", JSON.stringify(receipt, null, 2) + "\n");
console.log(JSON.stringify(receipt, null, 2));
if (receipt.classification !== "SOURCE_PASS") process.exit(2);
