import {junctionMap} from './junction-map.mjs';
import { el, put, setOptions, showLink, start, table } from './ui.mjs';
import { periods } from './model.mjs';
start(data => {
  const sites = Object.keys(data.sites), projects = Object.keys(data.projects);
  const measures = ['All reported crashes','Casualty crashes'];
  setOptions('first',[...projects,...sites.filter(s => !projects.includes(s))],projects[0]);
  setOptions('second',measures,measures[0]);
  setOptions('year',data.years, String(data.projects[projects[0]].year));
  el('first').addEventListener('change',()=>{
    const project = data.projects[el('first').value];
    if (project && data.years.includes(project.year)) el('year').value = String(project.year);
  });
  const drawMap = junctionMap(data.locations || {}, name => {
    el('first').value = name;
    el('first').dispatchEvent(new Event('change',{bubbles:true}));
  });
  const countSite = '208 ST & 88 AVE & TURNING LANE';
  el('turnexample').addEventListener('click',()=>{
    el('search').value = '';
    setOptions('first',sites,countSite); render();
  });
  el('search').addEventListener('input',()=>{
    const filter = el('search').value.trim().toUpperCase();
    const matches = sites.filter(s => s.includes(filter));
    const prior = el('first').value;
    setOptions('first',matches,matches.includes(prior) ? prior : matches[0]);
    el('first').dispatchEvent(new Event('change',{bubbles:true}));
  });
  function render() {
    const site = el('first').value, ref = Number(el('year').value), counts = data.sites[site];
    const hasSite = Boolean(site);
    for (const node of el('explore').children) {
      if (!node.classList.contains('controls')) node.hidden = !hasSite;
    }
    if (!hasSite) {
      put('finding','No matching junction. Try a street number or a shorter road name.'); el('finding').hidden = false;
      return;
    }
    drawMap(site, el('search').value, Array.from(el('first').options, option => option.value));
    put('turns', site === countSite
      ? 'Township engineers counted more than 400 northbound right turns per peak hour and more than 400 eastbound right turns per peak hour in early 2025. They counted 203 pedestrians at the north crosswalk over eight hours. The report gives a threshold for vehicles and a count for pedestrians.'
      : 'This edition has no matched turning count for this junction. The Township published a count for 208 Street at 88 Avenue. A junction-wide traffic rate would require counts from every approach over comparable periods.');
    el('turnlink').hidden = site !== countSite;
    el('turnexample').hidden = site === countSite;
    const idx = measures.indexOf(el('second').value), project = data.projects[site];
    const periodsToShow = periods(data.years,counts,ref,idx);
    periodsToShow.forEach(({years,mean},i)=>{
      put('label'+(i+1),(i ? 'After ' : 'Before ') + ref + ' · ' + years + (years === 1 ? ' year' : ' years'));
      put('value'+(i+1),mean === null ? 'Unavailable' : mean.toFixed(1) + ' / year');
    });
    put('finding', 'Average annual ' + measures[idx].toLowerCase() + '. ' +
        (project?.year === ref ? 'The comparison excludes the city’s project year.' : 'The reference year is user-selected.'));
    table('history',['Year','Reported crashes','Casualty crashes'],data.years.map((y,i)=>[y,...counts[i]]));
    put('project',project ? project.year + ' · ' + project.text : 'This edition has no documented project for this junction.');
    el('projectlink').hidden = !project;
    if (project) showLink('projectlink',project.url);
  }
  el('explore').addEventListener('change',render); render();
});
