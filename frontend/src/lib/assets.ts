// Paths of the rendered art (art/manifest.yaml -> frontend/public/assets).

const CARD_ASSETS: Record<string, string> = {
  container: "item.container",
  pike: "item.pike",
  link: "item.chain",
  blade: "weapon.blade",
  knife: "weapon.knife",
  cap: "acc.cap",
  bandana: "acc.bandana",
  necklace: "acc.necklace",
  watch: "acc.watch",
  boots: "acc.boots",
  ring: "acc.ring",
  gold_tooth: "rare.gold_tooth",
  universal_handle: "rare.handle",
  steel_wire: "rare.wire",
  phone: "rare.phone",
  fake_id: "rare.fake_id",
  shiv: "rare.shiv",
  spoon: "tool.spoon",
  pickaxe: "tool.pickaxe",
  shovel: "tool.shovel",
  shift_change: "action.shift_change",
  shortcut: "action.shortcut",
  package: "action.package",
  raid: "action.raid",
  bribe_money: "action.bribe",
  distraction: "action.distraction",
  first_aid: "action.first_aid",
  snitch: "action.snitch",
  cave_in: "action.cave_in",
};

export interface Img {
  src: string;
  srcSet: string;
}

function img(dir: string, id: string): Img {
  const base = `/assets/${dir}/${id}`;
  return { src: `${base}@2x.webp`, srcSet: `${base}@1x.webp 1x, ${base}@2x.webp 2x, ${base}@3x.webp 3x` };
}

export const assets = {
  place: (place: string) => img("places", `place.${place}`),
  portrait: (character: string) => img("characters", `${character}.portrait`),
  standee: (character: string) => img("characters", `${character}.standee`),
  pose: (character: string, pose: string) => img("characters", `${character}.pose.${pose}`),
  card: (cardDef: string) => img("cards", CARD_ASSETS[cardDef] ?? "item.container"),
  token: (token: string) => img("tokens", `token.${token}`),
  dice: (face: number) => img("dice", `dice.face${face}`),
  tunnel: (stage: number) => img("tunnel", `tunnel.stage${stage}`),
  logo: img("brand", "brand.logo"),
  board: img("board", "board"),
  gang: (gang: string) => img("gangs", `gang.${gang}`),
};

export const PLAYER_COLORS = ["#e0a33b", "#3fa7d6", "#c75b9b", "#59b36a", "#e05a47", "#9d7fe0"];
