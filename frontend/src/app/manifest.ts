import { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'Fragrance Finder - Luxury & Clone Price Tracker',
    short_name: 'FragranceFinder',
    description: 'Track designer and clone fragrance prices across discounters with live market comparisons.',
    start_url: '/',
    display: 'standalone',
    background_color: '#08080a',
    theme_color: '#08080a',
    orientation: 'portrait-primary',
    icons: [
      {
        src: '/icon-192.png',
        sizes: '192x192',
        type: 'image/png',
        purpose: 'any',
      },
      {
        src: '/icon-512.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'any',
      },
      {
        src: '/icon-maskable.png',
        sizes: '512x512',
        type: 'image/png',
        purpose: 'maskable',
      },
    ],
    categories: ['shopping', 'lifestyle'],
  };
}
