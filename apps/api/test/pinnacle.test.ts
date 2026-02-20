import test from "node:test";
import assert from "node:assert/strict";
import { americanToDecimal } from "../src/scraper.pinnacle.js";

test("americanToDecimal converts positive American odds", () => {
  assert.equal(americanToDecimal(150), 2.5);
  assert.equal(americanToDecimal(104), 2.04);
});

test("americanToDecimal converts negative American odds", () => {
  assert.equal(americanToDecimal(-110), 1.909);
  assert.equal(americanToDecimal(-200), 1.5);
});
