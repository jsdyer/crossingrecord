import {junctionMap} from './junction-map.mjs';
import { el, put, setOptions, showLink, start, table } from './ui.mjs';
import { periods } from './model.mjs';
start(data => {
  const sites = Object.keys(data.sites), projects = Object.keys(data.projects);
  const measures = ['All reported crashes','Casualty crashes'];
  const initial = new URLSearchParams(location.search);
  const selected = sites.includes(initial.get('junction')) ? initial.get('junction') : projects[0];
  setOptions('first',[...projects,...sites.filter(s => !projects.includes(s))],selected);
  setOptions('second',measures,initial.get('measure') === 'casualty' ? measures[1] : measures[0]);
  const year = Number(initial.get('year'));
  function yearOptions(site) {
    const pivot = data.projectProfiles?.[site]?.year;
    return pivot && !data.years.includes(pivot) ? [...data.years, pivot].sort((a,b) => a-b) : data.years;
  }
  const initialYears = yearOptions(selected);
  setOptions('year', initialYears, String(initialYears.includes(year) ? year : data.projects[selected]?.year ?? data.years.at(-1)));
  el('window').value = initial.get('window') === 'matched' ? 'matched' : 'all';
  el('first').addEventListener('change',()=>{
    const project = data.projects[el('first').value];
    const options = yearOptions(el('first').value);
    const prior = Number(el('year').value);
    setOptions('year', options, String(project && options.includes(project.year) ? project.year :
      options.includes(prior) ? prior : data.years.at(-1)));
  });
  const drawMap = junctionMap(data.locations || {}, name => {
    el('first').value = name;
    el('first').dispatchEvent(new Event('change',{bubbles:true}));
  });
  const countSite = '208 ST & 88 AVE & TURNING LANE';
  el('turnexample').addEventListener('click',()=>{
    el('search').value = '';
    setOptions('first',sites,countSite); el('first').dispatchEvent(new Event('change',{bubbles:true}));
  });
  el('search').addEventListener('input',()=>{
    const filter = el('search').value.trim().toUpperCase();
    const matches = sites.filter(s => s.includes(filter));
    const prior = el('first').value;
    setOptions('first',matches,matches.includes(prior) ? prior : matches[0]);
    el('first').dispatchEvent(new Event('change',{bubbles:true}));
  });
  function syncLocation(site) {
    const url = new URL(location.href);
    for (const key of ['junction', 'year', 'measure', 'window']) url.searchParams.delete(key);
    if (site) {
      url.searchParams.set('junction', site);
      url.searchParams.set('year', el('year').value);
      if (el('second').value === measures[1]) url.searchParams.set('measure', 'casualty');
      if (el('window').value === 'matched') url.searchParams.set('window', 'matched');
    }
    history.replaceState(null, '', url);
  }
  function render(updateURL = false) {
    const site = el('first').value, ref = Number(el('year').value), counts = data.sites[site];
    const hasSite = Boolean(site);
    for (const node of el('explore').children) {
      if (!node.classList.contains('controls')) node.hidden = !hasSite;
    }
    if (!hasSite) {
      put('finding','No matching junction. Try a street number or a shorter road name.'); el('finding').hidden = false;
      if (updateURL) syncLocation('');
      return;
    }
    put('current-junction', site);
    drawMap(site, el('search').value, Array.from(el('first').options, option => option.value));
    put('turns', site === countSite
      ? 'Township engineers counted more than 400 northbound right turns per peak hour and more than 400 eastbound right turns per peak hour in early 2025. They counted 203 pedestrians at the north crosswalk over eight hours. The report gives a threshold for vehicles and a count for pedestrians.'
      : 'This edition has no matched turning count for this junction. The Township published a count for 208 Street at 88 Avenue. A junction-wide traffic rate would require counts from every approach over comparable periods.');
    el('turnlink').hidden = site !== countSite;
    el('turnexample').hidden = site === countSite;
    const idx = measures.indexOf(el('second').value), project = data.projects[site];
    const profile = data.projectProfiles?.[site];
    el('window-control').hidden = !profile || profile.year !== ref;
    if (el('window-control').hidden) el('window').value = 'all';
    const matched = el('window').value === 'matched';
    const selectedYears = matched ? profile.pairedYears : data.years;
    const byYear = new Map(data.years.map((y, i) => [y, counts[i]]));
    const archive = data.projectArchive?.[site] || {};
    if (matched) for (const [y, item] of Object.entries(archive)) byYear.set(Number(y), item.counts);
    const selectedCounts = matched ? selectedYears.map(y => byYear.get(y)) : counts;
    const periodsToShow = periods(selectedYears,selectedCounts,ref,idx);
    el('profilelink').hidden = !profile;
    if (profile) showLink('profilelink', './' + profile.path);
    periodsToShow.forEach(({years,mean},i)=>{
      put('label'+(i+1),(i ? 'After ' : 'Before ') + ref + ' · ' + years + (years === 1 ? ' year' : ' years'));
      put('value'+(i+1),mean === null ? 'Unavailable' : mean.toFixed(1) + ' / year');
    });
    put('finding', 'Average ' + (idx ? 'casualty crashes' : 'reported crashes') + ' per year. ' +
        (matched ? 'Matched complete calendar years: ' + selectedYears.join(', ') + '. The project year is excluded.'
          : project?.year === ref ? 'The comparison excludes the city’s project year.' : 'The reference year is user-selected.'));
    table('history',['Year','Reported crashes','Casualty crashes'],[...byYear.keys()].sort((a,b) => a-b)
      .map(y => [archive[y] && !data.years.includes(y) ? y + ' · source checked ' + archive[y].retrieved : y, ...byYear.get(y)]));
    put('project',project ? project.year + ' · ' + project.text : 'This edition has no documented project for this junction.');
    el('projectlink').hidden = !project;
    if (project) showLink('projectlink',project.url);
    if (updateURL) syncLocation(site);
  }
  el('explore').addEventListener('change',() => render(true)); render();
});
