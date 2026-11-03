const state = {
  viewerId: localStorage.getItem("engage_viewer") || "U007",
  users: [],
  currentUser: null,
  feed: [],
  commentsPostId: null,
  profileUserId: null,
  chatPeerId: null,
  liveStories: [],
};

const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];

const icons = ["✦","◆","◈","✺","◉","⌘","△","✶","▣","⬡","◎","✹","◇","✷","◌","✧","◍","▦"];
const avatarText = name => (name || "?").split(/\s+/).map(x=>x[0]).join("").slice(0,2).toUpperCase();
const hue = seed => ((Number(seed)||1) * 47) % 360;
const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
const fmt = n => Number(n||0).toLocaleString();
const postIcon = p => icons[(Number(p.visual_seed)||1) % icons.length];

async function api(path, options={}) {
  const res = await fetch(path, {
    headers: {"Content-Type":"application/json", ...(options.headers||{})},
    ...options
  });
  const json = await res.json().catch(()=>({ok:false,error:"Invalid server response"}));
  if(!res.ok || !json.ok) throw new Error(json.error || `Request failed (${res.status})`);
  return json;
}

function toast(msg){
  const el=$("#toast"); el.textContent=msg; el.classList.add("show");
  clearTimeout(window.__toast); window.__toast=setTimeout(()=>el.classList.remove("show"),2200);
}

function avatar(user, cls=""){
  const color = user.avatar_color || user.creator_color || "#555";
  const name = user.user_name || user.creator_name || user.actor_name || "";
  return `<div class="avatar ${cls}" style="--avatar:${esc(color)}">${esc(avatarText(name))}</div>`;
}

function mediaStyle(seed){ return `--hue:${hue(seed)}`; }
function mediaContent(p){
  if(p.media_url){
    return `<img src="${esc(p.media_url)}" alt="Post image" onerror="this.onerror=null;this.src='/static/assets/study_table.svg'">`;
  }
  return `<div class="media-mark">${postIcon(p)}</div>`;
}

function formatCaption(text){
  return esc(text).replace(/(#[A-Za-z0-9_]+)/g,'<span class="hashtag">$1</span>');
}

function activateNav(name){
  $$(".nav-item[data-nav],.mobile-nav [data-nav]").forEach(b=>b.classList.toggle("active", b.dataset.nav===name));
}

async function navigate(name, extra={}){
  $$(".page").forEach(p=>p.classList.remove("active"));
  const page=$("#page-"+name);
  if(!page) return;
  page.classList.add("active"); activateNav(name);
  window.scrollTo({top:0,behavior:"smooth"});
  if(name==="home") await loadHome();
  if(name==="explore") { await loadExplore(); await loadRecentSearches(); }
  if(name==="activity") await loadActivity();
  if(name==="messages") await loadMessages();
  if(name==="profile") await loadProfile(extra.userId || state.viewerId);
  if(name==="analytics") await loadAnalytics();
  if(name==="recommendations") await loadRecommendations();
  if(name==="data") { await Promise.all([loadPostgresTable(), loadCourseFilters()]); await analyzeCourseDemand(); }
}

async function bootstrap(){
  try{
    const health=await api("/api/health");
    $("#dbDot").classList.add("online"); $("#dbText").textContent="ENGAGE DB connected";
    if(health.postgres?.connected){
      $("#pgDot").classList.add("online"); $("#pgText").textContent="PostgreSQL connected";
    }else{
      $("#pgDot").classList.remove("online"); $("#pgText").textContent="PostgreSQL unavailable";
    }
    const {data}=await api(`/api/bootstrap?viewer_id=${encodeURIComponent(state.viewerId)}`);
    state.users=data.users; state.currentUser=data.current_user;
    if(!state.currentUser && state.users.length){
      state.viewerId=state.users[0].user_id; localStorage.setItem("engage_viewer",state.viewerId);
      return bootstrap();
    }
    await renderStories();
    renderCurrentUser();
    renderSuggestions();
    await loadHome();
  }catch(e){
    $("#dbText").textContent="ENGAGE DB disconnected";
    $("#pgText").textContent="PostgreSQL status unknown";
    toast(e.message);
    $("#feed").innerHTML=`<div class="analytics-card"><h3>Database not connected</h3><p>Start PostgreSQL, check the POSTGRES_* values in .env, then refresh this page.</p></div>`;
  }
}

function setViewer(id){
  state.viewerId=id; localStorage.setItem("engage_viewer",id);
  bootstrap(); navigate("home");
}

function renderCurrentUser(){
  const u=state.currentUser; if(!u) return;
  $("#currentUserCard").innerHTML=`
    ${avatar(u)}
    <div class="user-copy click-user" data-user-id="${esc(u.user_id)}"><b>${esc(u.handle)}</b><small>${esc(u.user_name)}</small></div>
    <select class="viewer-select" id="viewerSelect">
      ${state.users.map(x=>`<option value="${esc(x.user_id)}" ${x.user_id===state.viewerId?"selected":""}>${esc(x.handle)}</option>`).join("")}
    </select>`;
  $("#viewerSelect").onchange=e=>setViewer(e.target.value);
}

async function renderStories(){
      let stories=[];
      try{
        const res=await api("/api/stories");
        stories=res.data||[];
      }catch{}
      state.liveStories=stories;
      const byUser={};
      for(const s of stories){ if(!byUser[s.user_id]) byUser[s.user_id]=s; }
      const ordered=[state.currentUser,...state.users.filter(u=>u.user_id!==state.viewerId)].filter(Boolean).slice(0,10);
      $("#stories").innerHTML=ordered.map(u=>{
        const st=byUser[u.user_id];
        const av = u.avatar_url
          ? `<div class="story-avatar" style="background-image:url('${esc(u.avatar_url)}')"></div>`
          : `<div class="story-avatar" style="--avatar:${esc(u.avatar_color)}">${esc(avatarText(u.user_name))}</div>`;
        return `<div class="story" data-story-user="${esc(u.user_id)}" data-story-id="${st?st.id:""}">
          <div class="story-ring">${av}</div>
          <div class="story-name">${esc(u.handle)}</div>
        </div>`;
      }).join("");
    }

async function renderSuggestions(){
  try{
    const {data}=await api(`/api/suggestions?viewer_id=${encodeURIComponent(state.viewerId)}`);
    const list=(data.resources||[]).slice(0,5);
    $("#suggestions").innerHTML=list.map(r=>{
      const cost=Number(r.monthly_cost||0)===0?"Free":`₹${fmt(r.monthly_cost)}/month`;
      return `<div class="suggestion learning-match-mini">
        <div class="resource-dot">${esc(String(r.recommendation_rank||"✦"))}</div>
        <div class="user-copy"><b>${esc(r.title)}</b><small>${esc(r.provider_name)} · ${cost}</small><small>${esc(r.recommendation_reason)}</small></div>
      </div>`;
    }).join("") || `<div class="rail-note">Add a learning profile to generate matches.</div>`;
  }catch(e){
    $("#suggestions").innerHTML=`<div class="rail-note">${esc(e.message)}</div>`;
  }
}

async function loadHome(){
  try{
    const {data}=await api(`/api/feed?viewer_id=${encodeURIComponent(state.viewerId)}`);
    state.feed=data; renderFeed(data);
    if(!data.length){
      $("#feed").innerHTML=`<div class="empty-social-state"><div class="empty-icon">◎</div><h3>Your feed is empty</h3><p>Run <code>python setup_postgres.py</code> and <code>python seed.py</code> once, then refresh.</p></div>`;
    }
  }catch(e){
    toast(e.message);
    $("#feed").innerHTML=`<div class="empty-social-state"><div class="empty-icon">!</div><h3>Feed could not load</h3><p>${esc(e.message)}</p></div>`;
  }
}

function renderFeed(posts){
  $("#feed").innerHTML=posts.map(p=>`
    <article class="post-card" data-post="${esc(p.post_id)}">
      <div class="post-head">
        ${avatar({user_name:p.creator_name,avatar_color:p.creator_color})}
        <div class="post-meta">
          <b class="click-user" data-user-id="${esc(p.creator_id)}">${esc(p.creator_handle)}</b>
          <small>${esc(p.location||"")}</small>
        </div><button class="more">•••</button>
      </div>
      <div class="post-media" style="${mediaStyle(p.visual_seed)}">
        ${mediaContent(p)}
        <div class="media-label">${esc((p.media_type||"post").toUpperCase())} · ${esc(p.genre)}</div>
        <div class="media-location">${esc(p.post_id)}</div>
      </div>
      <div class="post-actions">
        <button class="icon-btn ${p.viewer_liked?"active":""}" data-interaction="like" data-post="${esc(p.post_id)}">${p.viewer_liked?"♥":"♡"}</button>
        <button class="icon-btn" data-open-comments="${esc(p.post_id)}">◯</button>
        <button class="icon-btn" title="Copy link and count a share" data-share-post="${esc(p.post_id)}">↗</button>
        <button class="icon-btn ${p.viewer_reposted?"active":""}" data-interaction="repost" data-post="${esc(p.post_id)}">↻</button>
        <button class="icon-btn save ${p.viewer_saved?"active":""}" data-interaction="save" data-post="${esc(p.post_id)}">${p.viewer_saved?"▣":"▢"}</button>
      </div>
      <div class="post-stats">${fmt(p.likes)} likes · ${fmt(p.saves)} saves · ${fmt(p.reposts)} reposts · ${fmt(p.shares)} shares</div>
      <div class="caption"><span class="handle click-user" data-user-id="${esc(p.creator_id)}">${esc(p.creator_handle)}</span>${formatCaption(p.caption)}</div>
      <button class="view-comments" data-open-comments="${esc(p.post_id)}">View all ${fmt(p.comments)} comments</button>
      <div class="time">${esc(p.post_date)} · ${fmt(p.unique_reach)} unique reach</div>
    </article>`).join("");
  observeFeedPosts();
  const requestedPost = new URLSearchParams(window.location.search).get('post');
  if(requestedPost){
    const target = $$('.post-card[data-post]').find(card => card.dataset.post === requestedPost);
    if(target) requestAnimationFrame(() => target.scrollIntoView({behavior:'smooth',block:'center'}));
  }
}

const viewedThisLoad=new Set();
function observeFeedPosts(){
  const cards=$$(".post-card[data-post]");
  if(!("IntersectionObserver" in window)) return;
  const obs=new IntersectionObserver(entries=>{
    for(const entry of entries){
      const postId=entry.target.dataset.post;
      if(entry.isIntersecting && entry.intersectionRatio>=0.6 && !viewedThisLoad.has(postId)){
        viewedThisLoad.add(postId);
        setTimeout(()=>{
          api(`/api/post/${encodeURIComponent(postId)}/view`,{method:"POST",body:JSON.stringify({viewer_id:state.viewerId,dwell_seconds:2,completed:false})}).catch(()=>{});
        },1600);
        obs.unobserve(entry.target);
      }
    }
  },{threshold:[0.6]});
  cards.forEach(c=>obs.observe(c));
}

async function toggleInteraction(type,postId){
  try{
    const {data}=await api(`/api/post/${postId}/${type}`,{method:"POST",body:JSON.stringify({viewer_id:state.viewerId})});
    toast(data.active ? `${type} added` : `${type} removed`);
    await loadHome();
  }catch(e){toast(e.message)}
}

async function sharePostLink(postId){
  const url=`${window.location.origin}/?post=${encodeURIComponent(postId)}`;
  try{
    if(!navigator.clipboard || !navigator.clipboard.writeText){
      throw new Error("Your browser does not allow copying links here (try localhost or HTTPS).");
    }
    await navigator.clipboard.writeText(url);
    await api(`/api/post/${encodeURIComponent(postId)}/share`,{
      method:"POST",body:JSON.stringify({viewer_id:state.viewerId})
    });
    toast("Post link copied · share recorded");
    await loadHome();
  }catch(e){toast(e.message)}
}

async function toggleFollow(targetId){
  try{
    const {data}=await api(`/api/follow/${targetId}`,{method:"POST",body:JSON.stringify({viewer_id:state.viewerId})});
    toast(data.active?"Following user":"Unfollowed user");
    const b=await api(`/api/bootstrap?viewer_id=${encodeURIComponent(state.viewerId)}`);
    state.users=b.data.users; state.currentUser=b.data.current_user;
    renderSuggestions(); renderCurrentUser();
    if($("#page-profile").classList.contains("active")) await loadProfile(state.profileUserId||state.viewerId);
  }catch(e){toast(e.message)}
}

async function openComments(postId){
  state.commentsPostId=postId;
  $("#commentsModal").classList.remove("hidden");
  $("#commentsList").innerHTML="<p>Loading...</p>";
  try{
    const {data}=await api(`/api/comments/${postId}`);
    const byId=Object.fromEntries(data.map(c=>[c.comment_id,c]));
    $("#commentsList").innerHTML=data.length?data.map(c=>`
      <div class="comment-row">
        ${avatar(c,"small")}
        <div class="comment-body"><b class="click-user" data-user-id="${esc(c.user_id)}">${esc(c.handle)}</b> ${esc(c.comment_text)}
          ${c.parent_comment_id?`<small class="reply-chip">reply to ${esc(byId[c.parent_comment_id]?.handle||c.parent_comment_id)}</small>`:""}
          <small>${esc(c.sentiment)} · ${fmt(c.likes)} likes</small>
        </div>
      </div>`).join(""):`<p class="rail-note">No comments yet.</p>`;
  }catch(e){toast(e.message)}
}

async function loadExplore(){
  try{
    const {data}=await api(`/api/explore?viewer_id=${encodeURIComponent(state.viewerId)}`);
    $("#exploreGrid").innerHTML=data.map(p=>`
      <div class="explore-tile" style="${mediaStyle(p.visual_seed)}" data-post-preview="${esc(p.post_id)}">
        ${p.media_url?`<img src="${esc(p.media_url)}" alt="${esc(p.post_id)}" loading="lazy" onerror="this.onerror=null;this.src='/static/assets/photo_fallback.svg';">`:`<div class="tile-icon">${postIcon(p)}</div>`}
        <div class="tile-overlay"><span>♥ ${fmt(p.likes)}</span><span>◯ ${fmt(p.comments)}</span></div>
      </div>`).join("");
  }catch(e){toast(e.message)}
}

async function loadActivity(){
  try{
    const {data}=await api(`/api/notifications?viewer_id=${encodeURIComponent(state.viewerId)}`);
    $("#activityList").innerHTML=data.length?data.map(n=>`
      <div class="activity-row">
        ${avatar({user_name:n.actor_name,avatar_color:n.actor_color})}
        <div class="user-copy click-user" data-user-id="${esc(n.actor_id)}">
          <span><b>${esc(n.actor_handle)}</b> ${esc(n.text)}</span>
          <small>${n.comment_text?esc(n.comment_text):n.post_caption?esc(n.post_caption).slice(0,70):"ENGAGE DB activity"}</small>
        </div>
      </div>`).join(""):`<div class="analytics-card">No activity yet.</div>`;
  }catch(e){toast(e.message)}
}

async function loadProfile(userId){
  state.profileUserId=userId;
  try{
    const [profileRes,postsRes]=await Promise.all([
      api(`/api/profile/${userId}?viewer_id=${encodeURIComponent(state.viewerId)}`),
      api(`/api/feed?viewer_id=${encodeURIComponent(state.viewerId)}&profile_user_id=${encodeURIComponent(userId)}`)
    ]);
    const u=profileRes.data, posts=postsRes.data;
    const isMe=userId===state.viewerId;
    $("#profileHeader").innerHTML=`
      <div class="profile-hero">
        <div class="profile-avatar-wrap"><div class="profile-avatar" style="--avatar:${esc(u.avatar_color)}">${esc(avatarText(u.user_name))}</div></div>
        <div>
          <div class="profile-name-row"><h2>${esc(u.handle)}</h2>
            ${isMe?`<button class="soft-btn">Edit profile</button>`:`<button class="soft-btn follow-btn ${u.viewer_follows?"following":""}" data-follow="${esc(u.user_id)}">${u.viewer_follows?"Following":"Follow"}</button>`}
          </div>
          <div class="profile-stats"><span><b>${fmt(u.posts)}</b> posts</span><span><b>${fmt(u.followers)}</b> followers</span><span><b>${fmt(u.following)}</b> following</span></div>
          <div class="profile-bio"><b>${esc(u.user_name)}</b><br>${esc(u.bio)}<br><span class="rail-note">${esc(u.city)}</span></div>
        </div>
      </div>`;
    $("#profileGrid").innerHTML=posts.map(p=>`
      <div class="explore-tile" style="${mediaStyle(p.visual_seed)}">
        ${p.media_url?`<img src="${esc(p.media_url)}" alt="${esc(p.post_id)}" loading="lazy" onerror="this.onerror=null;this.src='/static/assets/photo_fallback.svg';">`:`<div class="tile-icon">${postIcon(p)}</div>`}
        <div class="tile-overlay"><span>♥ ${fmt(p.likes)}</span><span>◯ ${fmt(p.comments)}</span></div>
      </div>`).join("");
  }catch(e){toast(e.message)}
}

function renderBars(rows,key,labelKey,target){
  const max=Math.max(...rows.map(x=>Number(x[key]||0)),1);
  $(target).innerHTML=rows.map(r=>`
    <div class="rank-row">
      <div><div>${esc(r[labelKey])}</div><div class="rank-bar"><span style="width:${(Number(r[key]||0)/max)*100}%"></span></div></div>
      <div class="rank-value">${fmt(r[key])}</div>
    </div>`).join("");
}

async function loadAnalytics(){
  try{
    const {data}=await api("/api/analytics");
    const s=data.summary;
    const cards=[
      ["Users",s.users],["Posts",s.posts],["Likes",s.likes],["Saves",s.saves],
      ["Reposts",s.reposts],["Comments",s.comments],["Hashtags",s.hashtags],["Impressions",s.impressions]
    ];
    $("#analyticsSummary").innerHTML=cards.map(([k,v])=>`<div class="stat-card"><small>${k}</small><b>${fmt(v)}</b></div>`).join("");
    renderBars(data.top_posts,"likes","post_id","#topPosts");
    renderBars(data.hashtags,"engagement","hashtag","#topHashtags");
    renderBars(data.top_users,"followers","handle","#topUsers");
    $("#sentimentChart").innerHTML=data.sentiments.map(x=>`<div class="sentiment-pill ${esc(x.sentiment)}"><span>${esc(x.sentiment)}</span><b>${fmt(x.count)}</b></div>`).join("");
  }catch(e){toast(e.message)}
}

function renderTable(el,rows){
  if(!rows.length){$(el).innerHTML="<div class='analytics-card'>No records.</div>";return}
  const keys=Object.keys(rows[0]);
  $(el).innerHTML=`<div class="table-wrap"><table><thead><tr>${keys.map(k=>`<th>${esc(k.replaceAll("_"," "))}</th>`).join("")}</tr></thead>
  <tbody>${rows.map(r=>`<tr>${keys.map(k=>`<td>${esc(r[k])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

async function loadData(){
  try{
    const entity=$("#dataSelect").value;
    const {data}=await api(`/api/data/${entity}`);
    renderTable("#dataTable",data);
  }catch(e){toast(e.message)}
}

async function loadGraph(){
  try{
    const {data}=await api("/api/graph");
    const svg=$("#graphView"), W=900,H=520,cx=W/2,cy=H/2;
    const nodes=data.nodes.map((n,i)=>{
      const a=(i/data.nodes.length)*Math.PI*2;
      const ring=n.type==="User"?145:n.type==="Post"?220:280;
      return {...n,x:cx+Math.cos(a)*ring+(i%3)*8,y:cy+Math.sin(a)*ring+(i%4)*6};
    });
    const map=Object.fromEntries(nodes.map(n=>[n.id,n]));
    const colors={User:"#ff4f8b",Post:"#7b61ff",Hashtag:"#39d9a0"};
    const lines=data.links.map(l=>{
      const a=map[l.source],b=map[l.target]; if(!a||!b)return"";
      return `<line class="graph-link" x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}"/>`;
    }).join("");
    const circles=nodes.map(n=>`<g class="graph-node"><circle cx="${n.x}" cy="${n.y}" r="${n.type==="User"?9:7}" fill="${colors[n.type]||"#aaa"}"/><text x="${n.x+10}" y="${n.y+3}">${esc(n.label)}</text></g>`).join("");
    svg.innerHTML=lines+circles;
  }catch(e){toast(e.message)}
}


async function showStory(userId){
  const u=state.users.find(x=>x.user_id===userId); if(!u)return;
  const st=(state.liveStories||[]).find(x=>x.user_id===userId);
  let latest=null;
  if(!st){
    try{ latest=(await api(`/api/feed?viewer_id=${state.viewerId}&profile_user_id=${userId}`)).data[0] }catch{}
  }
  const media=st?.media_url
    ? `<img src="${esc(st.media_url)}" style="width:100%;height:100%;object-fit:cover;position:absolute;inset:0;opacity:.65">`
    : "";
  const caption=st?.caption || latest?.caption || u.bio;
  $("#storyContent").innerHTML=`<div class="story-visual" style="${mediaStyle(latest?.visual_seed||userId.charCodeAt(userId.length-1))}">
    ${media}
    <div class="story-center" style="position:relative;z-index:1">${avatar(u)}<h2>@${esc(u.handle)}</h2><p>${formatCaption(caption||"")}</p></div>
  </div>`;
  $("#storyModal").classList.remove("hidden");
}

async function doSearch(q){
  const box=$("#searchResults");
  if(q.trim().length<2){box.classList.add("hidden");return}
  try{
    const {data}=await api(`/api/search?q=${encodeURIComponent(q)}&viewer_id=${encodeURIComponent(state.viewerId)}`);
    box.innerHTML=`
      <div class="search-section"><h4>Users</h4>${data.users.map(u=>`<div class="search-item click-user" data-user-id="${esc(u.user_id)}">@${esc(u.handle)} · ${esc(u.user_name)}</div>`).join("")||"<div class='search-item'>No users</div>"}</div>
      <div class="search-section"><h4>Hashtags</h4>${data.hashtags.map(h=>`<div class="search-item">${esc(h.hashtag)} · ${fmt(h.posts)} posts</div>`).join("")||"<div class='search-item'>No hashtags</div>"}</div>
      <div class="search-section"><h4>Posts</h4>${data.posts.map(p=>`<div class="search-item">${esc(p.post_id)} · ${esc(p.caption).slice(0,65)}</div>`).join("")||"<div class='search-item'>No posts</div>"}</div>`;
    box.classList.remove("hidden");
  }catch(e){toast(e.message)}
}


let sqlExamples=[];
async function loadSQLExamples(){
  if(sqlExamples.length)return;
  try{const {data}=await api("/api/sql/examples");sqlExamples=data;$("#sqlExampleSelect").innerHTML=`<option value="">Choose an example query...</option>`+data.map((x,i)=>`<option value="${i}">${esc(x.name)}</option>`).join("");}catch(e){toast(e.message)}
}
function renderSQLSummary(summary){
  const target=$("#sqlSummary");if(!summary){target.classList.add("hidden");return}
  const fields=[["SQL type",summary.query_type||"-"],["Rows changed",summary.properties_set||0],["Time",`${summary.result_consumed_after_ms??0} ms`]];
  target.innerHTML=fields.filter(([,v],i)=>i!==1||Number(v)!==0).map(([k,v])=>`<span class="summary-chip">${esc(k)}: <b>${esc(v)}</b></span>`).join("");target.classList.remove("hidden");
}
async function runSQLConsole(){
  const query=$("#sqlInput").value.trim();if(!query){toast("Enter an SQL query first");return}
  $("#sqlStatus").textContent="Running...";$("#sqlResult").innerHTML=`<div class="sql-message">Executing query...</div>`;$("#sqlSummary").classList.add("hidden");
  try{const res=await api("/api/sql",{method:"POST",body:JSON.stringify({query,viewer_id:state.viewerId})});const rows=res.data||[];renderSQLSummary(res.summary);$("#sqlStatus").textContent=`Success · ${rows.length} row${rows.length===1?"":"s"}`;
    if(rows.length){const keys=[...new Set(rows.flatMap(r=>Object.keys(r)))];$("#sqlResult").innerHTML=`<div class="table-wrap"><table><thead><tr>${keys.map(k=>`<th>${esc(k.replaceAll("_"," "))}</th>`).join("")}</tr></thead><tbody>${rows.map(r=>`<tr>${keys.map(k=>`<td>${esc(typeof r[k]==="object"&&r[k]!==null?JSON.stringify(r[k]):r[k])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;}else{$("#sqlResult").innerHTML=`<div class="sql-message">Query executed successfully. No rows were returned.</div>`;}
    await loadQueryHistory();
    if(res.summary?.contains_updates){const b=await api(`/api/bootstrap?viewer_id=${encodeURIComponent(state.viewerId)}`);state.users=b.data.users;state.currentUser=b.data.current_user;renderStories();renderCurrentUser();renderSuggestions();toast("Database updated");}
  }catch(e){$("#sqlStatus").textContent="Error";$("#sqlResult").innerHTML=`<div class="sql-message sql-error">${esc(e.message)}</div>`;}
}

async function loadRecommendations(){
  const notice=$("#recommendationStorageNotice");
  $("#recommendedResources").innerHTML="<p class='rail-note'>Generating learning matches...</p>";
  $("#recommendedUsers").innerHTML="<p class='rail-note'>Loading community...</p>";
  $("#recommendedPosts").innerHTML="<p class='rail-note'>Generating...</p>";
  $("#recommendedHashtags").innerHTML="<p class='rail-note'>Generating...</p>";
  try{
    const {data}=await api(`/api/suggestions?viewer_id=${encodeURIComponent(state.viewerId)}`);
    notice.className="storage-notice "+(data.postgres_persisted?"good":"warn");
    notice.textContent=data.postgres_persisted
      ?"Learning matches use live PostgreSQL engagement + the student-selected goal/budget, and are persisted for the DBMS demo."
      :"PostgreSQL is required for recommendations in this single-database build.";

    const pref=data.preferences||{};
    $("#recommendationMode").value=pref.recommendation_mode||"balanced";
    $("#preferredGenres").value=(pref.preferred_genres||[]).join(", ");
    $("#preferredHashtags").value=(pref.preferred_hashtags||[]).join(", ");
    const profile=data.profile||{};
    $("#academicStage").value=profile.academic_stage||"Class 12";
    $("#examGoal").value=profile.exam_goal||"JEE";
    $("#maxMonthlyBudget").value=profile.max_monthly_budget??0;
    $("#budgetPreference").value=profile.budget_preference||"balanced";
    $("#preferredMode").value=profile.preferred_mode||"online";
    if(typeof setPreferenceSaveState === "function") setPreferenceSaveState("Loaded saved profile from PostgreSQL", "good");

    const feedback=(type,key)=>`
      <div class="feedback-actions">
        <button class="interested-btn" data-suggestion-feedback="interested" data-suggestion-type="${type}" data-target-key="${esc(key)}">Interested</button>
        <button class="notinterested-btn" data-suggestion-feedback="not_interested" data-suggestion-type="${type}" data-target-key="${esc(key)}">Not interested</button>
      </div>`;

    $("#recommendedResources").innerHTML=(data.resources||[]).map(r=>{
      const cost=Number(r.monthly_cost||0)===0?"Free":`₹${fmt(r.monthly_cost)}/month`;
      return `<div class="resource-match-card">
        <div class="resource-match-top"><b>#${esc(r.recommendation_rank)} ${esc(r.title)}</b><span>${esc(String(r.total_score))}/100</span></div>
        <small>${esc(r.provider_name)} · ${esc(r.delivery_mode)} · ${cost}</small>
        <p>${esc(r.recommendation_reason)}</p>
        <div class="score-chips"><span>interest ${esc(r.interest_score)}</span><span>affordability ${esc(r.affordability_score)}</span><span>goal ${esc(r.goal_score)}</span></div>
      </div>`;
    }).join("") || "<p class='rail-note'>No learning matches yet. Set your exam goal and budget above.</p>";

    $("#recommendedUsers").innerHTML=(data.users||[]).map(u=>`
      <div class="suggestion-row">
        ${avatar({user_name:u.user_name,avatar_color:u.avatar_color},"small")}
        <div class="suggestion-copy"><b>@${esc(u.handle)}</b><small>${esc(u.reason)}</small>${feedback("user",u.user_id)}</div>
        <div class="suggestion-actions"><button class="follow-btn" data-follow="${esc(u.user_id)}">Follow</button></div>
      </div>`).join("") || "<p class='rail-note'>No new people suggestions.</p>";

    $("#recommendedPosts").innerHTML=(data.posts||[]).map(p=>`
      <div class="recommended-post">
        <div class="recommended-post-visual" style="${mediaStyle(p.visual_seed)}">${p.media_url?`<img src="${esc(p.media_url)}" style="width:100%;height:100%;object-fit:cover;border-radius:10px">`:postIcon(p)}</div>
        <div class="suggestion-copy"><b>${esc(p.post_id)} · @${esc(p.creator_handle)}</b><small>${esc(p.reason)}</small>${feedback("post",p.post_id)}</div>
      </div>`).join("") || "<p class='rail-note'>No post suggestions.</p>";

    $("#recommendedHashtags").innerHTML=(data.hashtags||[]).map(h=>`
      <div class="suggestion-row">
        <div class="suggestion-copy"><b>${esc(h.hashtag)}</b><small>${esc(h.reason)}</small>${feedback("hashtag",h.hashtag)}</div>
      </div>`).join("") || "<p class='rail-note'>No hashtag suggestions.</p>";
  }catch(e){
    notice.className="storage-notice warn";
    notice.textContent=e.message;
  }
}

async function dismissSuggestion(type,key){
  try{
    await api("/api/suggestions/status",{method:"POST",body:JSON.stringify({
      viewer_id:state.viewerId,suggestion_type:type,target_key:key,status:"dismissed"
    })});
    toast("Suggestion dismissed");
    await loadRecommendations();
  }catch(e){toast(e.message)}
}

async function suggestSQL(){
  const q=$("#sqlIntent").value.trim();
  if(!q){toast("Describe what query you need");return}
  try{
    const {data}=await api(`/api/sql/suggest?q=${encodeURIComponent(q)}`);
    $("#sqlSuggestions").innerHTML=data.map((x,i)=>`
      <div class="sql-suggestion">
        <span><b>${esc(x.name)}</b> · score ${esc(x.score)}</span>
        <button data-use-suggested-query="${i}">Use</button>
      </div>`).join("");
    window.__sqlSuggested=data;
  }catch(e){toast(e.message)}
}

async function saveCurrentSQL(){
  const query=$("#sqlInput").value.trim();
  if(!query){toast("Enter a query first");return}
  const title=prompt("Name this saved query:", "My SQL query");
  if(!title)return;
  try{
    await api("/api/saved-queries",{method:"POST",body:JSON.stringify({
      viewer_id:state.viewerId,title,query_text:query,category:"demo"
    })});
    toast("Saved in PostgreSQL");
    await loadSavedQueries();
  }catch(e){toast(e.message)}
}

async function loadSavedQueries(){
  try{
    const {data}=await api(`/api/saved-queries?viewer_id=${encodeURIComponent(state.viewerId)}`);
    $("#savedQueriesList").innerHTML=data.map(x=>`
      <div class="mini-list-item">
        <b>${esc(x.title)}</b><small>${esc(x.category)} · ${esc(x.created_at)}</small>
        <div class="mini-list-actions">
          <button data-load-saved-query="${x.id}" data-query="${encodeURIComponent(x.query_text)}">Load</button>
          <button data-delete-saved-query="${x.id}">Delete</button>
        </div>
      </div>`).join("") || "<div class='rail-note'>No saved queries yet.</div>";
  }catch(e){
    $("#savedQueriesList").innerHTML="<div class='rail-note'>PostgreSQL not connected.</div>";
  }
}

async function loadQueryHistory(){
  try{
    const {data}=await api(`/api/query-history?viewer_id=${encodeURIComponent(state.viewerId)}`);
    $("#queryHistoryList").innerHTML=data.map(x=>`
      <div class="mini-list-item">
        <b>${x.success?"✓":"✕"} ${esc(x.query_text).slice(0,80)}</b>
        <small>${esc(x.executed_at)} · ${x.row_count} row(s)</small>
        <div class="mini-list-actions"><button data-load-history-query="${encodeURIComponent(x.query_text)}">Load</button></div>
      </div>`).join("") || "<div class='rail-note'>No query history yet.</div>";
  }catch(e){
    $("#queryHistoryList").innerHTML="<div class='rail-note'>PostgreSQL not connected.</div>";
  }
}

async function loadPostgresQueryPanels(){
  await Promise.all([loadSavedQueries(),loadQueryHistory()]);
}

async function deleteSavedQuery(id){
  try{
    await api(`/api/saved-queries/${id}?viewer_id=${encodeURIComponent(state.viewerId)}`,{method:"DELETE"});
    toast("Saved query deleted");
    await loadSavedQueries();
  }catch(e){toast(e.message)}
}
function setPreferenceSaveState(message, kind="neutral"){
  const el = $("#preferencesSaveState");
  if(!el) return;
  el.textContent = message;
  el.className = `save-state ${kind}`;
}

function markPreferencesDirty(){
  const btn = $("#savePreferences");
  if(btn) btn.disabled = false;
  setPreferenceSaveState("Unsaved changes", "warn");
}

async function savePreferences(){
  const genres=$("#preferredGenres").value.split(",").map(x=>x.trim()).filter(Boolean);
  const hashtags=$("#preferredHashtags").value.split(",").map(x=>x.trim()).filter(Boolean);
  const mode=$("#recommendationMode").value;
  const btn = $("#savePreferences");
  if(btn){ btn.disabled = true; btn.textContent = "Saving..."; }
  setPreferenceSaveState("Saving your profile to PostgreSQL…", "pending");
  try{
    await api("/api/preferences",{method:"POST",body:JSON.stringify({
      viewer_id:state.viewerId,
      preferred_genres:genres,
      preferred_hashtags:hashtags,
      recommendation_mode:mode
    })});
    await api("/api/student-profile",{method:"POST",body:JSON.stringify({
      viewer_id:state.viewerId,
      academic_stage:$("#academicStage").value.trim()||"Class 12",
      exam_goal:$("#examGoal").value.trim()||"JEE",
      max_monthly_budget:Number($("#maxMonthlyBudget").value||0),
      budget_preference:$("#budgetPreference").value,
      preferred_mode:$("#preferredMode").value,
      language_preference:"English",
      city:state.currentUser?.city||""
    })});
    const goalField = $("#courseSearch");
    if(goalField && !goalField.value.trim()) goalField.value = $("#examGoal").value.trim() || "JEE";
    if(typeof loadCourseFilters === "function") await loadCourseFilters();
    if(typeof analyzeCourseDemand === "function" && $("#courseSearch")?.value.trim()) await analyzeCourseDemand();
    toast("Learning profile saved in PostgreSQL");
    setPreferenceSaveState("Saved successfully · PostgreSQL updated", "good");
    await loadRecommendations();
  }catch(e){
    setPreferenceSaveState(`Save failed: ${e.message}`, "error");
    toast(e.message)
  }finally{
    if(btn){ btn.disabled = false; btn.textContent = "Save Profile"; }
  }
}

async function sendSuggestionFeedback(type,key,feedback){
  try{
    await api("/api/suggestions/feedback",{method:"POST",body:JSON.stringify({
      viewer_id:state.viewerId,
      suggestion_type:type,
      target_key:key,
      feedback
    })});
    toast(feedback==="interested"?"Preference recorded":"Suggestion hidden");
    await loadRecommendations();
  }catch(e){toast(e.message)}
}

async function loadPostgresTable(){
  const target=$("#postgresTableData");
  const table=$("#postgresTableSelect").value;
  target.innerHTML="<div class='sql-message'>Loading PostgreSQL...</div>";
  try{
    const {data}=await api(`/api/postgres/table/${table}`);
    renderTable("#postgresTableData",data);
  }catch(e){
    target.innerHTML=`<div class="sql-message sql-error">${esc(e.message)}</div>`;
  }
}


async function uploadSelectedImage(){
  const file=$("#postImageFile").files[0];
  if(!file) return null;
  $("#uploadStatus").textContent="Uploading image...";
  const form=new FormData();
  form.append("file",file);
  const res=await fetch("/api/upload",{method:"POST",body:form});
  const data=await res.json();
  if(!res.ok || !data.ok) throw new Error(data.error||"Image upload failed");
  $("#uploadStatus").textContent="Image ready";
  return data.data.media_url;
}
async function loadMessages(){
  $("#messageUserSelect").innerHTML=state.users.filter(u=>u.user_id!==state.viewerId)
    .map(u=>`<option value="${esc(u.user_id)}">@${esc(u.handle)}</option>`).join("");
  try{
    const {data}=await api(`/api/messages/conversations?viewer_id=${encodeURIComponent(state.viewerId)}`);
    $("#conversationList").innerHTML=data.length?data.map(c=>{
      const u=c.user||{user_id:c.peer_id,user_name:c.peer_id,handle:c.peer_id,avatar_color:"#555"};
      return `<div class="conversation-item ${state.chatPeerId===c.peer_id?"active":""}" data-chat-user="${esc(c.peer_id)}">
        ${avatar(u,"small")}
        <div class="conversation-copy"><b>@${esc(u.handle)}</b><small>${esc(c.last_message||"")}</small></div>
        ${Number(c.unread_count)>0?`<span class="unread-badge">${c.unread_count}</span>`:""}
      </div>`;
    }).join(""):`<div class="rail-note" style="padding:16px">No messages yet. Choose a user above.</div>`;
    if(state.chatPeerId) await openChat(state.chatPeerId);
  }catch(e){
    $("#conversationList").innerHTML=`<div class="rail-note" style="padding:16px">PostgreSQL is required for messages.</div>`;
  }
}

async function openChat(peerId){
  state.chatPeerId=peerId;
  const peer=state.users.find(u=>u.user_id===peerId);
  $("#chatHeader").innerHTML=peer?`@${esc(peer.handle)} · ${esc(peer.user_name)}`:esc(peerId);
  $("#chatMessages").innerHTML="<div class='rail-note'>Loading...</div>";
  try{
    const {data}=await api(`/api/messages/${peerId}?viewer_id=${encodeURIComponent(state.viewerId)}`);
    $("#chatMessages").innerHTML=data.length?data.map(m=>`
      <div class="message-bubble ${m.sender_id===state.viewerId?"mine":"theirs"}">
        ${esc(m.body)}
        <small>${esc(m.sent_at)}</small>
      </div>`).join(""):`<div class="rail-note">Start the conversation.</div>`;
    $("#chatMessages").scrollTop=$("#chatMessages").scrollHeight;
    $$(".conversation-item").forEach(x=>x.classList.toggle("active",x.dataset.chatUser===peerId));
  }catch(e){toast(e.message)}
}

async function sendChatMessage(){
  const input=$("#messageInput"),body=input.value.trim();
  if(!body||!state.chatPeerId)return;
  try{
    await api(`/api/messages/${state.chatPeerId}`,{method:"POST",body:JSON.stringify({viewer_id:state.viewerId,body})});
    input.value="";
    await openChat(state.chatPeerId);
    await loadMessages();
  }catch(e){toast(e.message)}
}

async function loadRecentSearches(){
  try{
    const {data}=await api(`/api/recent-searches?viewer_id=${encodeURIComponent(state.viewerId)}`);
    $("#recentSearches").innerHTML=data.length
      ? `<span class="rail-note">Recent:</span>`+data.map(x=>`<button class="recent-search-chip" data-recent-search="${encodeURIComponent(x.search_text)}">${esc(x.search_text)}</button>`).join("")
      : "";
  }catch{$("#recentSearches").innerHTML=""}
}

async function loadAppEvents(){
  try{
    const {data}=await api(`/api/app-events?viewer_id=${encodeURIComponent(state.viewerId)}`);
    $("#appEventsList").innerHTML=data.map(x=>`
      <div class="mini-list-item">
        <div class="event-line"><b>${esc(x.event_type)}</b><span>${esc(x.created_at)}</span></div>
        <small>${esc(x.target_type||"")} ${esc(x.target_key||"")}</small>
      </div>`).join("") || "<div class='rail-note'>No events yet.</div>";
  }catch(e){
    $("#appEventsList").innerHTML="<div class='rail-note'>PostgreSQL not connected.</div>";
  }
}

async function createStory(){
  const caption=$("#storyCaption").value.trim();
  let media_url=null;
  const file=$("#storyImageFile").files[0];
  if(file){
    $("#storyUploadStatus").textContent="Uploading...";
    const form=new FormData(); form.append("file",file);
    const res=await fetch("/api/upload",{method:"POST",body:form});
    const data=await res.json();
    if(!res.ok||!data.ok) throw new Error(data.error||"Upload failed");
    media_url=data.data.media_url;
  }
  await api("/api/stories",{method:"POST",body:JSON.stringify({viewer_id:state.viewerId,caption,media_url})});
  $("#storyCreateModal").classList.add("hidden");
  $("#createStoryForm").reset();
  $("#storyUploadStatus").textContent="";
  $("#storyCreatePreview").innerHTML="<span>Story preview</span>";
  await renderStories();
  toast("Story shared for 24 hours");
}
document.addEventListener("click",async e=>{
  const nav=e.target.closest("[data-nav]"); if(nav){navigate(nav.dataset.nav);return}
  const action=e.target.closest("[data-action]");
  if(action){
    if(action.dataset.action==="open-create") $("#createModal").classList.remove("hidden");
    if(action.dataset.action==="close-create") $("#createModal").classList.add("hidden");
    if(action.dataset.action==="open-story-create") $("#storyCreateModal").classList.remove("hidden");
    if(action.dataset.action==="close-story-create") $("#storyCreateModal").classList.add("hidden");
    if(action.dataset.action==="close-comments") $("#commentsModal").classList.add("hidden");
    if(action.dataset.action==="close-story") $("#storyModal").classList.add("hidden");
    return;
  }
  const user=e.target.closest("[data-user-id]"); if(user){await navigate("profile",{userId:user.dataset.userId});return}
  const follow=e.target.closest("[data-follow]"); if(follow){await toggleFollow(follow.dataset.follow);return}
  const share=e.target.closest("[data-share-post]"); if(share){await sharePostLink(share.dataset.sharePost);return}
  const inter=e.target.closest("[data-interaction]"); if(inter){await toggleInteraction(inter.dataset.interaction,inter.dataset.post);return}
  const comments=e.target.closest("[data-open-comments]"); if(comments){await openComments(comments.dataset.openComments);return}
  const story=e.target.closest("[data-story-user]"); if(story){showStory(story.dataset.storyUser);return}
  const chat=e.target.closest("[data-chat-user]"); if(chat){await openChat(chat.dataset.chatUser);return}
  const rs=e.target.closest("[data-recent-search]"); if(rs){$("#searchInput").value=decodeURIComponent(rs.dataset.recentSearch); await doSearch($("#searchInput").value); return}
  const dis=e.target.closest("[data-dismiss-suggestion]"); if(dis){await dismissSuggestion(dis.dataset.dismissSuggestion,dis.dataset.targetKey);return}
  const sq=e.target.closest("[data-use-suggested-query]"); if(sq){const x=(window.__sqlSuggested||[])[Number(sq.dataset.useSuggestedQuery)]; if(x){$("#sqlInput").value=x.query; toast("Suggested SQL query loaded");} return}
  const saved=e.target.closest("[data-load-saved-query]"); if(saved){$("#sqlInput").value=decodeURIComponent(saved.dataset.query); toast("Saved query loaded"); return}
  const hist=e.target.closest("[data-load-history-query]"); if(hist){$("#sqlInput").value=decodeURIComponent(hist.dataset.loadHistoryQuery); toast("History query loaded"); return}
  const del=e.target.closest("[data-delete-saved-query]"); if(del){await deleteSavedQuery(del.dataset.deleteSavedQuery);return}
  const fb=e.target.closest("[data-suggestion-feedback]"); if(fb){await sendSuggestionFeedback(fb.dataset.suggestionType,fb.dataset.targetKey,fb.dataset.suggestionFeedback);return}
});

$("#createCaption")?.addEventListener("input",e=>{$("#createPreview span").textContent=e.target.value||"Share something with ENGAGE DB"});
$("#createPostForm")?.addEventListener("submit",async e=>{
  e.preventDefault(); const body=Object.fromEntries(new FormData(e.target).entries()); body.viewer_id=state.viewerId;
  try{
    body.media_url=await uploadSelectedImage();
    await api("/api/post",{method:"POST",body:JSON.stringify(body)});
    $("#createModal").classList.add("hidden"); e.target.reset(); $("#uploadStatus").textContent=""; $("#createPreview span").textContent="Share something with ENGAGE DB";
    toast("Post shared"); await loadHome(); await bootstrap();
  }catch(err){toast(err.message)}
});
$("#commentForm")?.addEventListener("submit",async e=>{
  e.preventDefault(); const input=$("#commentInput"),text=input.value.trim(); if(!text)return;
  try{
    await api(`/api/post/${state.commentsPostId}/comment`,{method:"POST",body:JSON.stringify({viewer_id:state.viewerId,comment_text:text})});
    input.value=""; toast("Comment added"); await openComments(state.commentsPostId); await loadHome();
  }catch(err){toast(err.message)}
});
let searchTimer;
$("#searchInput")?.addEventListener("input",e=>{clearTimeout(searchTimer);searchTimer=setTimeout(()=>doSearch(e.target.value),220)});
document.addEventListener("keydown",e=>{if(e.key==="Escape"){$$(".modal-backdrop").forEach(m=>m.classList.add("hidden"));$("#searchResults").classList.add("hidden")}});


$("#refreshRecommendations")?.addEventListener("click",loadRecommendations);


$("#postImageFile")?.addEventListener("change",e=>{
  const file=e.target.files[0];
  if(!file) return;
  const url=URL.createObjectURL(file);
  $("#createPreview").innerHTML=`<img src="${url}" alt="Preview">`;
});
$("#savePreferences")?.addEventListener("click",savePreferences);
["#academicStage","#examGoal","#maxMonthlyBudget","#budgetPreference","#preferredMode","#preferredGenres","#preferredHashtags","#recommendationMode"].forEach(sel=>{ const el=$(sel); if(el){ el.addEventListener("input",markPreferencesDirty); el.addEventListener("change",markPreferencesDirty); }});
$("#postgresTableSelect")?.addEventListener("change",loadPostgresTable);
$("#refreshPostgresTable")?.addEventListener("click",loadPostgresTable);
$("#startConversation")?.addEventListener("click",async()=>{
  state.chatPeerId=$("#messageUserSelect").value;
  await openChat(state.chatPeerId);
});
$("#messageForm")?.addEventListener("submit",async e=>{e.preventDefault();await sendChatMessage()});
$("#createStoryForm")?.addEventListener("submit",async e=>{
  e.preventDefault();
  try{await createStory()}catch(err){toast(err.message)}
});
$("#storyImageFile")?.addEventListener("change",e=>{
  const file=e.target.files[0]; if(!file)return;
  const url=URL.createObjectURL(file);
  $("#storyCreatePreview").innerHTML=`<img src="${url}" alt="Story preview">`;
});

bootstrap();
