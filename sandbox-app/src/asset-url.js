// Public assets must resolve beneath the deployed site, including project subpaths.
export function assetUrl(path,base=import.meta.env?.BASE_URL??'/'){
  return base+path.replace(/^\/+/, '');
}
