async function api(path,method="GET",data){
 const r=await fetch(path,{method,headers:{"Content-Type":"application/json"},body:data?JSON.stringify(data):undefined});
 const x=await r.json();if(!r.ok)throw Error(x.error||"Request failed");return x;
}
function esc(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
async function refresh(){
 const d=await api("/api/dashboard");
 const metrics=[["Stores",d.stores],["Inventory records",d.inventory_records],["Low-stock items",d.low_stock_items],["Open cases",d.open_cases],["Pending approvals",d.pending_approvals],["Replenishment requests",d.replenishment_requests]];
 document.querySelector("#metrics").innerHTML=metrics.map(x=>`<div class="metric"><span>${x[0]}</span><strong>${x[1]}</strong></div>`).join("");
 const [reps,inv,cases,notes,audit]=await Promise.all([api("/api/replenishments"),api("/api/inventory"),api("/api/cases"),api("/api/notifications"),api("/api/audit")]);
 document.querySelector("#replenishments").innerHTML=reps.replenishments.map(x=>{
  const pending=x.status==="Pending Approval";
  return `<tr><td>#${x.id}</td><td>${esc(x.store)} / ${esc(x.product)}</td><td>${esc(x.sku)}</td><td>${x.quantity}</td><td><span class="pill ${x.status==="Approved"?"approved":x.status==="Rejected"?"rejected":"pending"}">${esc(x.status)}</span></td><td>${esc(x.decided_by||"—")}</td><td>${pending?`<button class="action" onclick="decide(${x.id},'approve')">Approve</button><button class="action reject" onclick="decide(${x.id},'reject')">Reject</button>`:"—"}</td></tr>`;
 }).join("")||'<tr><td colspan="7">No requests yet. Run the low-stock flow.</td></tr>';
 document.querySelector("#inventory").innerHTML=inv.inventory.map(x=>`<tr><td>${esc(x.store)}</td><td>${esc(x.sku)}</td><td>${esc(x.product)}</td><td>${x.on_hand}</td><td>${x.reorder_level}</td><td class="${x.on_hand<x.reorder_level?'low':'ok'}">${x.on_hand<x.reorder_level?'Reorder':'Healthy'}</td></tr>`).join("");
 document.querySelector("#cases").innerHTML=cases.cases.map(x=>`<tr><td>#${x.id}</td><td>${esc(x.store)}</td><td>${esc(x.category)}</td><td>${esc(x.severity)}</td><td>${esc(x.status)}</td></tr>`).join("")||'<tr><td colspan="5">No cases yet</td></tr>';
 document.querySelector("#notifications").innerHTML=notes.notifications.map(x=>`<div class="feedItem">${esc(x.message)}<small>${esc(x.event_type)} · ${esc(x.created_at)}</small></div>`).join("")||"No notifications yet.";
 document.querySelector("#audit").innerHTML=audit.audit.map(x=>`<tr><td>${esc(x.created_at)}</td><td>${esc(x.action)}</td><td>${esc(x.entity_type)}</td><td>${x.entity_id}</td><td>${esc(x.actor)}</td><td>${esc(x.details)}</td></tr>`).join("")||'<tr><td colspan="6">No audit events yet</td></tr>';
}
async function decide(id,decision){
 const manager=prompt("Manager name:");if(!manager)return;
 const reason=prompt(decision==="reject"?"Reason for rejection (required):":"Approval note (optional):")||"";
 if(decision==="reject"&&!reason.trim()){alert("Please provide a rejection reason.");return;}
 try{const x=await api(`/api/replenishments/${id}/decision`,"POST",{decision,manager,reason});alert(`Request #${id} ${x.status.toLowerCase()}.`);await refresh();}
 catch(e){alert(e.message);}
}
document.querySelector("#runAuto").addEventListener("click",async()=>{
 const b=document.querySelector("#runAuto");b.disabled=true;
 try{const x=await api("/api/automation/replenishment","POST",{});document.querySelector("#autoMsg").textContent=`${x.created_count} new request(s) created. Active duplicate protection is on.`;await refresh();}
 catch(e){document.querySelector("#autoMsg").textContent=e.message;}finally{b.disabled=false;}
});
document.querySelector("#caseForm").addEventListener("submit",async e=>{
 e.preventDefault();const data=Object.fromEntries(new FormData(e.target));
 try{const x=await api("/api/cases","POST",data);document.querySelector("#caseMsg").textContent=`Case #${x.id} created · ${x.tasks_created} tasks · ${x.approval_required?"manager approval required":"standard routing"}`;await refresh();}
 catch(err){document.querySelector("#caseMsg").textContent=err.message;}
});
document.querySelector("#refresh").addEventListener("click",refresh);
refresh().catch(e=>console.error(e));
