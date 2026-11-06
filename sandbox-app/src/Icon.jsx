import React from 'react';

// One small, local icon family for the guide; no external font or icon request.
export function Icon({name,...props}){
  const paths={
    sun:<><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.4 1.4m11.2 11.2L19 19M5 19l1.4-1.4M17.6 6.4 19 5"/></>,
    moon:<path d="M20.5 13.1A8.6 8.6 0 0 1 10.9 3.5a8.6 8.6 0 1 0 9.6 9.6Z"/>,
    plus:<path d="M12 5v14M5 12h14"/>,minus:<path d="M5 12h14"/>,
    reset:<><path d="M4 10a8 8 0 1 1 1 8M4 4v6h6"/></>,
    arrow:<path d="M5 12h14m-5-5 5 5-5 5"/>,
    close:<path d="m6 6 12 12M18 6 6 18"/>,
    layers:<><path d="m3 7 9-4 9 4-9 4-9-4Zm0 5 9 4 9-4M3 17l9 4 9-4"/></>,
    compass:<><circle cx="12" cy="12" r="9"/><path d="m16 8-3 5-5 3 3-5 5-3Z"/></>,
    search:<><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></>,
    list:<><path d="M8 6h12M8 12h12M8 18h12M3 6h1M3 12h1M3 18h1"/></>,
    book:<><path d="M12 5v15M3 4h5c2 0 4 1 4 2 0-1 2-2 4-2h5v14h-5c-2 0-4 1-4 2 0-1-2-2-4-2H3V4Z"/></>,
    rotate:<><path d="M4 9a8 8 0 0 1 14-3l2 3M20 4v5h-5M20 15a8 8 0 0 1-14 3l-2-3M4 20v-5h5"/></>,
    move:<><path d="M12 3v18M3 12h18m-12-6 3-3 3 3m-6 12 3 3 3-3M6 9l-3 3 3 3m12-6 3 3-3 3"/></>,
    pin:<><path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 0 1 14 0Z"/><circle cx="12" cy="10" r="2"/></>,
    expand:<><path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5"/></>,
    city:<><path d="M2 20h20M4 20V9l5-3v14M9 20V3h6v17m0-10h5v10M11 7h2m-2 4h2m-2 4h2"/></>
  };
  return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name]}</svg>;
}
