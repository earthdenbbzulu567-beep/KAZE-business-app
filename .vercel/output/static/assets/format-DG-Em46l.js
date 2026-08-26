function e(){let e=new Date;return`${e.getFullYear()}-${String(e.getMonth()+1).padStart(2,`0`)}-${String(e.getDate()).padStart(2,`0`)}`}function t(e,t=`$`,n){let r=Math.abs(e).toLocaleString(`en-US`,{minimumFractionDigits:2,maximumFractionDigits:2});if(n?.signed){if(e<0)return`-${t}${r}`;if(e>0)return`+${t}${r}`}return e<0?`-${t}${r}`:`${t}${r}`}var n=[`Food`,`Rent`,`Supplies`,`Marketing`,`Utilities`,`Transport`,`Wages`,`Other`];function r(e,t,n){let r=e=>`"${e.replaceAll(`"`,`""`)}"`,i=[t.map(r).join(`,`),...n.map(e=>e.map(r).join(`,`))].join(`
`),a=new Blob([i],{type:`text/csv;charset=utf-8`}),o=URL.createObjectURL(a),s=document.createElement(`a`);s.href=o,s.download=e,s.click(),URL.revokeObjectURL(o)}function i(e,t){let n=document.createElement(`iframe`);n.style.position=`fixed`,n.style.right=`0`,n.style.bottom=`0`,n.style.width=`0`,n.style.height=`0`,n.style.border=`0`,document.body.appendChild(n);let r=n.contentDocument;r&&(r.open(),r.write(`<!doctype html><html><head><title>${e}</title>
    <style>
      body { font-family: Georgia, serif; color: #111; padding: 32px; }
      h1 { font-size: 22px; margin: 0 0 4px; }
      .muted { color: #555; font-size: 13px; }
      table { width: 100%; border-collapse: collapse; margin-top: 20px; }
      th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #ddd; font-size: 13px; }
      th { text-transform: uppercase; letter-spacing: .06em; font-size: 11px; color: #666; }
      .total { font-weight: 700; }
      pre { white-space: pre-wrap; font-family: Georgia, serif; }
    </style></head><body>${t}</body></html>`),r.close(),n.onload=()=>{n.contentWindow?.focus(),n.contentWindow?.print(),setTimeout(()=>n.remove(),500)})}export{e as a,i,r as n,t as r,n as t};