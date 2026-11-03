/* ENGAGE V11 — accessible live course discovery, no meter / compass. */
const courseIntelligence = {lastDemand:null,filtersLoaded:false,initialized:false,trending:null};
const rsNumber=n=>Number(n||0).toLocaleString('en-IN');
const rsMoney=n=>Number(n||0).toLocaleString('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0});
const rsPercent=n=>`${Number(n||0).toFixed(1)}%`;

async function loadCourseFilters(){
  try{
    const {data}=await api('/api/studio/course-filters');
    const hints=$('#courseGoalHints');
    if(hints) hints.innerHTML=data.goals.map(g=>`<option value="${esc(g)}"></option>`).join('');
    const profiles=$('#courseProfileSelect');
    if(profiles){
      const selected=profiles.value||state.viewerId;
      profiles.innerHTML=data.students.map(s=>`<option value="${esc(s.user_id)}">${esc(s.user_name)} · ${esc(s.exam_goal)} · ${esc(rsMoney(s.max_monthly_budget))}/month</option>`).join('');
      if(data.students.some(s=>s.user_id===selected))profiles.value=selected;
      else if(data.students.some(s=>s.user_id===state.viewerId))profiles.value=state.viewerId;
    }
    const select=$('#trendingGoalFilter');
    if(select){
      const chosen=select.value;
      select.innerHTML='<option value="all">All courses</option>'+data.goals.map(g=>`<option value="${esc(g)}">${esc(g)}</option>`).join('');
      if([...select.options].some(x=>x.value===chosen))select.value=chosen;
    }
    courseIntelligence.filtersLoaded=true;
  }catch(e){if($('#courseDemandStatus'))$('#courseDemandStatus').textContent='Could not load course filters: '+e.message;}
}

function demandUi(data){
  if(!data.matched_goals.length)return `<div class="course-empty">No matching goal or topic: <strong>${esc(data.query)}</strong>. Try JEE, NEET, GATE, CAT, UPSC, CUET or IELTS.</div>`;
  return `<div class="course-summary-head"><div><span class="course-summary-eyebrow">AUDIENCE SNAPSHOT</span><h4>${esc(data.matched_goals.join(' · '))}</h4><small>Based on ${rsNumber(data.total_students)} student profiles · Budget ≥ ${rsMoney(data.minimum_budget)}/month</small></div><span class="course-live-pill">● PostgreSQL</span></div>
    <div class="course-metric-grid course-metric-v11">
      <div class="course-metric"><span>Students with this goal</span><strong>${rsNumber(data.goal_students)}</strong><small>Potential audience</small></div>
      <div class="course-metric featured"><span>Share of all students</span><strong>${rsPercent(data.goal_percentage)}</strong><small>${rsNumber(data.goal_students)} of ${rsNumber(data.total_students)} profiles</small></div>
      <div class="course-metric"><span>Budget-qualified students</span><strong>${rsNumber(data.qualified_students)}</strong><small>Goal + stated budget</small></div>
      <div class="course-metric"><span>Qualified within goal</span><strong>${rsPercent(data.qualified_within_goal_percentage)}</strong><small>Among goal-matched students</small></div>
    </div>
    <p class="course-gauge-footnote">These are self-reported interest and affordability matches—not guaranteed course enrollments. Update student profiles to see these figures change.</p>`;
}

async function analyzeCourseDemand(){
  const course=$('#courseSearch')?.value.trim();const budget=$('#courseBudget')?.value.trim();
  if(!course){$('#courseDemandStatus').textContent='Enter a course or exam goal.';$('#courseSearch').focus();return;}
  if(budget===''||!Number.isFinite(Number(budget))||Number(budget)<0){$('#courseDemandStatus').textContent='Enter a valid budget greater than or equal to zero.';return;}
  $('#courseDemandStatus').textContent='Reading live student profiles…';
  const button=$('#courseDemandButton');button.disabled=true;
  try{
    const q=new URLSearchParams({course,budget});
    const {data}=await api('/api/studio/course-demand?'+q);
    courseIntelligence.lastDemand=data;
    $('#courseDemandResults').innerHTML=demandUi(data);
    $('#courseDemandStatus').textContent=`Updated · ${rsNumber(data.total_students)} profiles · Search: ${data.query}`;
  }catch(e){$('#courseDemandResults').innerHTML=`<div class="course-empty course-error">${esc(e.message)}</div>`;$('#courseDemandStatus').textContent='Could not calculate demand';}
  finally{button.disabled=false;}
}

function courseActivityBreakdown(x){
  return `<span title="Likes">♥ ${rsNumber(x.likes)}</span><span title="Shares">↗ ${rsNumber(x.shares)}</span><span title="Comments">◯ ${rsNumber(x.comments)}</span><span title="Saves">▣ ${rsNumber(x.saves)}</span><span title="Reposts">↻ ${rsNumber(x.reposts)}</span>`;
}
function trendingEntry(r,i){return `<article class="course-rank-item"><span class="course-rank-number">${i+1}</span>
  <div class="course-rank-main"><strong>${esc(r.title)}</strong><div class="course-subline">${esc(r.provider_name)} · ${esc(r.exam_goal)} · ${esc(r.topic)} · ${rsMoney(r.monthly_cost)}/month</div>
  <div class="course-activity">${courseActivityBreakdown(r)}</div></div>
  <span class="course-rank-score">${rsNumber(r.trending_score)} <small>points</small></span></article>`;}

function renderTrending(){
  const results=$('#courseTrendingResults');const data=courseIntelligence.trending;
  if(!data||!results)return;
  const goal=$('#trendingGoalFilter')?.value||'all', sort=$('#trendingSort')?.value||'score';
  let rows=data.resources.filter(r=>goal==='all'||r.exam_goal.toLowerCase()===goal.toLowerCase());
  const sortFns={
    score:(a,b)=>Number(b.trending_score)-Number(a.trending_score),
    likes:(a,b)=>Number(b.likes)-Number(a.likes),
    comments:(a,b)=>Number(b.comments)-Number(a.comments),
    saves:(a,b)=>Number(b.saves)-Number(a.saves),
    priceLow:(a,b)=>Number(a.monthly_cost)-Number(b.monthly_cost),
    priceHigh:(a,b)=>Number(b.monthly_cost)-Number(a.monthly_cost)
  };
  rows=rows.slice().sort((a,b)=>(sortFns[sort]||sortFns.score)(a,b)||Number(b.trending_score)-Number(a.trending_score)||String(a.title).localeCompare(String(b.title)));
  const goals=data.goals.slice().sort((a,b)=>Number(b.trending_score)-Number(a.trending_score));
  results.innerHTML=`<div class="course-result-subtitle">${rsNumber(rows.length)} course listings · ${goal==='all'?'All exam goals':esc(goal)}</div>`+
    (rows.length?rows.map(trendingEntry).join(''):'<div class="course-empty">No courses match this filter.</div>')+
    '<div class="course-result-subtitle">Goal popularity by weighted engagement</div>'+
    goals.map((g,i)=>`<div class="course-goal-row"><span>${i+1}. <b>${esc(g.exam_goal)}</b></span><span>${rsNumber(g.post_count)} posts · <b>${rsNumber(g.trending_score)} points</b></span></div>`).join('')+
    `<p class="course-fine-print">${esc(data.note)}</p>`;
}
async function loadCourseTrending(){
  $('#courseTrendingResults').innerHTML='<div class="course-empty">Loading trending posts and interactions…</div>';
  try{const {data}=await api('/api/studio/trending');courseIntelligence.trending=data;renderTrending();}
  catch(e){$('#courseTrendingResults').innerHTML=`<div class="course-empty course-error">${esc(e.message)}</div>`;}
}
async function searchAffordableCourse(){
  const course=$('#findCourseSearch').value.trim(),user_id=$('#courseProfileSelect').value;
  const el=$('#courseFinderResults');
  if(!course||!user_id){el.innerHTML='<div class="course-empty">Enter a course name and choose a student.</div>';return;}
  const q=new URLSearchParams({course,user_id,sort:$('#courseFinderSort').value,mode:$('#courseFinderMode').value});
  el.innerHTML='<div class="course-empty">Finding affordable courses using this student’s saved monthly budget…</div>';
  try{
    const {data}=await api('/api/studio/find-course?'+q);
    el.innerHTML=`<div class="course-finder-summary"><b>${esc(data.profile.user_name)}</b> · ${esc(data.profile.exam_goal)} · Budget up to <b>${rsMoney(data.profile.max_monthly_budget)}/month</b><div><strong>${rsNumber(data.available_count)} matching course${data.available_count===1?'':'s'}</strong> · sorted by ${esc($('#courseFinderSort').selectedOptions[0].textContent)}</div></div>`+
      (data.resources.length?data.resources.map((r,i)=>`<article class="course-found-item"><div class="course-found-top"><strong>${i+1}. ${esc(r.title)}</strong><b>${rsMoney(r.monthly_cost)}/mo</b></div><div class="course-subline">${esc(r.provider_name)} · ${esc(r.exam_goal)} / ${esc(r.topic)} · ${esc(r.delivery_mode)}</div><p>${esc(r.description||'Course information')}</p><div class="course-activity">${courseActivityBreakdown(r)} <strong>Trending score: ${rsNumber(r.trending_score)}</strong></div></article>`).join(''):'<div class="course-empty">No affordable courses matched. Try another exam, mode or student.</div>')+`<p class="course-fine-print">${esc(data.note)}</p>`;
  }catch(e){el.innerHTML=`<div class="course-empty course-error">${esc(e.message)}</div>`;}
}
function initCourseStudio(){
  if(courseIntelligence.initialized)return;courseIntelligence.initialized=true;
  loadCourseFilters().then(()=>{if($('#courseSearch')?.value)analyzeCourseDemand();});
}
$('#courseDemandForm')?.addEventListener('submit',e=>{e.preventDefault();analyzeCourseDemand();});
$('#findTrendingBtn')?.addEventListener('click',()=>{$('#courseTrendingPanel').classList.remove('hidden');$('#courseFinderPanel').classList.add('hidden');loadCourseTrending();});
$('#findCourseBtn')?.addEventListener('click',async()=>{$('#courseFinderPanel').classList.remove('hidden');$('#courseTrendingPanel').classList.add('hidden');if(!courseIntelligence.filtersLoaded)await loadCourseFilters();const field=$('#findCourseSearch');if(!field.value)field.value=$('#courseSearch').value;field.focus();});
$('#courseFinderForm')?.addEventListener('submit',e=>{e.preventDefault();searchAffordableCourse();});
$('#courseFinderSort')?.addEventListener('change',()=>{if($('#courseFinderResults')?.innerHTML.includes('course-finder-summary'))searchAffordableCourse();});
$('#courseFinderMode')?.addEventListener('change',()=>{if($('#courseFinderResults')?.innerHTML.includes('course-finder-summary'))searchAffordableCourse();});
$('#trendingGoalFilter')?.addEventListener('change',renderTrending);
$('#trendingSort')?.addEventListener('change',renderTrending);
document.querySelectorAll('[data-course-close]').forEach(b=>b.addEventListener('click',()=>document.getElementById(b.dataset.courseClose)?.classList.add('hidden')));
document.addEventListener('DOMContentLoaded',initCourseStudio);
