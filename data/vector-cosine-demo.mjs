// vector-cosine-demo.mjs — runnable teaching demo of vector search
// run:  node data/vector-cosine-demo.mjs "AI ช่วยงานวิจัย"
// ARRA Oracle workshop · /loop vector-teaching · iteration 3
//
// Real production uses 1024-dim embeddings (bge-m3) from an embedder model.
// Here we hand-craft 4-dim vectors [health, ai, edu, climate] to TEACH the math —
// the ranking logic is identical to the real thing.

const DOCS = [
  { t: "โรคเบาหวาน",              v: [0.90, 0.10, 0.05, 0.05] },
  { t: "การรักษามะเร็ง",           v: [0.95, 0.05, 0.00, 0.05] },
  { t: "วัคซีน",                  v: [0.85, 0.10, 0.10, 0.00] },
  { t: "สาธารณสุข (public health)", v: [0.80, 0.10, 0.20, 0.10] },
  { t: "machine learning",       v: [0.05, 0.95, 0.20, 0.00] },
  { t: "AI agent",               v: [0.00, 0.98, 0.10, 0.00] },
  { t: "vector database",        v: [0.05, 0.90, 0.10, 0.00] },
  { t: "การสอนออนไลน์",           v: [0.10, 0.30, 0.90, 0.00] },
  { t: "pedagogy / การศึกษา",     v: [0.15, 0.15, 0.92, 0.00] },
  { t: "น้ำท่วม",                 v: [0.20, 0.05, 0.05, 0.90] },
  { t: "climate change",         v: [0.05, 0.15, 0.05, 0.95] },
];

// pretend-embedder: map a known query phrase to a vector.
// (real system: call bge-m3 / CF Workers AI to embed ANY text)
const QVEC = {
  "เบาหวาน":         [0.88, 0.10, 0.05, 0.05],
  "AI ช่วยงานวิจัย":  [0.10, 0.90, 0.25, 0.00],
  "สอนนักศึกษา":     [0.10, 0.20, 0.92, 0.00],
  "โลกร้อน":         [0.10, 0.10, 0.05, 0.93],
};

// the ONE formula behind vector search
function cosine(a, b) {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) { dot += a[i] * b[i]; na += a[i] * a[i]; nb += b[i] * b[i]; }
  return dot / (Math.sqrt(na) * Math.sqrt(nb));
}

function search(queryVec, topK = 3) {
  return DOCS
    .map(d => ({ t: d.t, score: cosine(queryVec, d.v) }))
    .sort((a, b) => b.score - a.score)
    .slice(0, topK);
}

const q = process.argv[2] || "AI ช่วยงานวิจัย";
const qv = QVEC[q] || QVEC["AI ช่วยงานวิจัย"];
console.log(`\nค้น: "${q}"  →  ใกล้ที่สุดตามความหมาย (cosine similarity):\n`);
for (const [i, r] of search(qv).entries()) {
  console.log(`  ${i + 1}. ${r.t.padEnd(24)}  ${(r.score * 100).toFixed(1)}%`);
}
console.log(`\n(สังเกต: ผลลัพธ์ไม่มีคำตรงกับคำค้นเลย — แต่ความหมายใกล้)\n`);
