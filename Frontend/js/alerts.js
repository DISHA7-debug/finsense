import { getAlerts } from "./api.js";

const table =
document.getElementById("alertsTable");

const filter =
document.getElementById("tierFilter");

let alerts=[];

document.addEventListener("DOMContentLoaded",loadAlerts);

async function loadAlerts(){

    try{

        alerts=await getAlerts();

        render(alerts);

    }

    catch(err){

        console.error(err);

    }

}

filter.addEventListener("change",()=>{

    const tier=filter.value;

    if(tier==="all"){

        render(alerts);

        return;

    }

    render(

        alerts.filter(

            a=>a.tier.toLowerCase()===tier

        )

    );

});

function render(data){

    table.innerHTML="";

    data.forEach(alert=>{

        table.innerHTML+=`

<tr>

<td>

${alert.borrower_name}

</td>

<td>

${alert.loan_type}

</td>

<td>

${alert.score}

</td>

<td>

<span class="badge ${alert.tier.toLowerCase()}">

${alert.tier}

</span>

</td>

<td>

${new Date(alert.created_at).toLocaleDateString()}

</td>

<td>

<button

class="btn-brand px-4 py-2 rounded-lg"

onclick="window.location='borrower.html?loan=${alert.loan_id}'">

Open

</button>

</td>

</tr>

`;

    });

}