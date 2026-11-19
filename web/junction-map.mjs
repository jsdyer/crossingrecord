import {streetMap} from './streets.mjs';

export function junctionMap(coordinates, choose) {
  const map = L.map('junction-map', {scrollWheelZoom:false, minZoom:8, maxZoom:19})
    .setView([49.1,-122.59],11);
  streetMap(map).addTo(map);
  L.control.scale({imperial:false}).addTo(map);
  const markers = L.featureGroup().addTo(map);
  const ordinary = {color:'#fff', weight:1.4, fillColor:'#156c79', fillOpacity:.85, radius:5};
  const active = {color:'#fff', weight:2.5, fillColor:'#a13e13', fillOpacity:1, radius:9};
  let oldSearch, previousSite;
  const lookup = new Map();
  document.getElementById('fit-junctions').onclick = () => {
    if (markers.getBounds().isValid()) map.fitBounds(markers.getBounds(), {padding:[18,18], maxZoom:16, animate:false});
  };
  return function render(site, search, matches) {
    map.invalidateSize({pan:false});
    if (search !== oldSearch) {
      oldSearch = search;
      markers.clearLayers(); lookup.clear();
      for (const name of matches) {
        const locations = coordinates[name] || [];
        const pins = locations.map(point => {
          const label = document.createElement('span');
          label.textContent = name;
          return L.circleMarker(point, ordinary).bindTooltip(label)
            .on('click', () => choose(name)).addTo(markers);
        });
        lookup.set(name, pins);
      }
      previousSite = null;
    }
    if (previousSite === site) return;
    for (const pin of lookup.get(previousSite) || []) pin.setStyle(ordinary).setRadius(ordinary.radius);
    previousSite = site;
    const current = lookup.get(site) || [];
    for (const pin of current) pin.setStyle(active).setRadius(active.radius).bringToFront();
    document.getElementById('fit-junctions').disabled = !markers.getLayers().length;
    const note = document.getElementById('junction-location');
    if (!current.length) {
      note.textContent = 'ICBC has no mapped coordinate for this junction.';
      if (markers.getBounds().isValid()) map.fitBounds(markers.getBounds(), {maxZoom:15, animate:false});
      return;
    }
    map.fitBounds(L.latLngBounds(current.map(pin => pin.getLatLng())), {maxZoom:16, padding:[25,25], animate:false});
    note.textContent = site + ' · ' + current.length + (current.length === 1 ? ' published location.' : ' published locations share this exact junction label.');
  };
}
