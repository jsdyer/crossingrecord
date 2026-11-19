export function periods(years, counts, pivot, index) {
  const summarize = values => ({years:values.length, mean:values.length ? values.reduce((a,b)=>a+b,0)/values.length : null});
  const before = [], after = [];
  years.forEach((year,i) => {
    if (year < pivot) before.push(counts[i][index]);
    if (year > pivot) after.push(counts[i][index]);
  });
  return [summarize(before),summarize(after)];
}
