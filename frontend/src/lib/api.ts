const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export function getToken(){ if(typeof window==="undefined") return ""; return localStorage.getItem("talentiq_token") || ""; }
export async function api(path:string, options:RequestInit={}) {
  const headers = new Headers(options.headers || {});
  const token=getToken();
  if(token) headers.set("Authorization",`Bearer ${token}`);
  if(options.body && !(options.body instanceof FormData)) headers.set("Content-Type","application/json");
  const response=await fetch(`${BASE}${path}`,{...options,headers,cache:"no-store"});
  const data=await response.json().catch(()=>({detail:"Unexpected server response"}));
  if(!response.ok) throw new Error(data.detail || "Request failed");
  return data;
}
export async function login(email:string,password:string){
  const r=await fetch(`${BASE}/api/v1/auth/login`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email,password})});
  const d=await r.json(); if(!r.ok) throw new Error(d.detail || "Login failed");
  localStorage.setItem("talentiq_token",d.access_token); return d.user;
}
