import { _ as e, l as s, H as n, e as i, I as p } from "./index-CTgvlc8H.js";
import { p as g } from "./treemap-75Q7IDZK-BYqNGg4h.js";
import "./_baseUniq-o7e9QmIE.js";
import "./_basePickBy-UWsuIbv6.js";
import "./clone-CEDDMd2u.js";
var v = { parse: e(async (r) => {
  const a = await g("info", r);
  s.debug(a);
}, "parse") }, d = { version: p.version + "" }, m = e(() => d.version, "getVersion"), c = { getVersion: m }, l = e((r, a, o) => {
  s.debug(`rendering info diagram
` + r);
  const t = n(a);
  i(t, 100, 400, true), t.append("g").append("text").attr("x", 100).attr("y", 40).attr("class", "version").attr("font-size", 32).style("text-anchor", "middle").text(`v${o}`);
}, "draw"), f = { draw: l }, S = { parser: v, db: c, renderer: f };
export {
  S as diagram
};
