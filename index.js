var express = require("express");
const cors = require('cors')
const spawn = require("child_process").spawn;
const fs = require('fs');


var app = express();
app.use(cors())
app.use(express.json());

const directoryPath = "./champions";

let filesNames = fs.readdirSync(directoryPath).map(fileName => {
    return fileName.toString().slice(0, fileName.length - ".json".length)
  });

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


function isJsonString(str) {
    try {
        JSON.parse(str);
    } catch (e) {
        return false;
    }
    return true;
}


async function getRawChampionData(name){
    file = "./champions/" + name + ".json"

    var obj = JSON.parse(fs.readFileSync(file, 'utf8'));

    return obj
}

function flatten(data, sub){
    for (const [key, value] of Object.entries(data[sub])) {
        data[key] = data[sub][key]
    }
    delete data[sub]
}


async function getCleanChampionData(name, tier){
    let data = await getRawChampionData(name)
    tier = tier.toUpperCase()

    delete data["name"]
    delete data["id"]
    delete data["key"]
    delete data["partype"]
    flatten(data, "info")
    flatten(data, "stats")
    for (const [key, value] of Object.entries(data["gamestats"][tier])) {
        data[key] = data["gamestats"][tier][key]
    }
    delete data["gamestats"]

    data["Tank"] = data["tags"].filter((tag) => tag == "Tank").length
    data["Fighter"] = data["tags"].filter((tag) => tag == "Fighter").length
    data["Assassin"] = data["tags"].filter((tag) => tag == "Assassin").length
    data["Mage"] = data["tags"].filter((tag) => tag == "Mage").length
    data["Support"] = data["tags"].filter((tag) => tag == "Support").length
    data["Marksman"] = data["tags"].filter((tag) => tag == "Marksman").length

    delete data["tags"]

    while (true){
        for (const [key, value] of Object.entries(data)) {
            if(key.substring(0, "total_".length) === "total_" || key.substring(0, "frequency_".length) === "frequency_"){
                delete data[key]
                break
            }
        }

        let b = true
        for (const [key, value] of Object.entries(data)) {
            if(key.substring(0, "total_".length) === "total_" || key.substring(0, "frequency_".length) === "frequency_"){
                b = false
                break
            }
        }
        if(b){
            break
        }
    }
    
    delete data["gamesrecorded"]

    return data
}

async function get_match(t, participants){
    let jsm = {"tier": t}
    for(let i = 0; i < participants.length; i++) {
        let base_n = "participant_" + (i + 1).toString() + "_"
        let clean_p = await getCleanChampionData(participants[i], t)
        for (const [key, value] of Object.entries(clean_p)) {
            jsm[base_n + key] = value
        }
    }
    return jsm
}


app.post("/api/champs", async (req, res, next) => {
    console.log(req.body);
    // await sleep(1000);
    // check request body for correct data
    if("tier" in req.body == false || "participants" in req.body == false) {
        return res.status(400).send({
            message: 'tier and participants are required',
            status_code: 400
         });
    }
    participantsAreValid = true
    participants = req.body["participants"]
    participants.forEach(participant => {
        if(!filesNames.includes(participant)) {
            participantsAreValid = false;
        }
    })

    if(!participantsAreValid){
        console.log("invalid participant")
        return res.status(400).send({
            message: 'invalid participant',
            status_code: 400
         });
    }

    var d = await get_match(req.body["tier"], [req.body["participants"][0], req.body["participants"][1], req.body["participants"][2], req.body["participants"][3], req.body["participants"][4], req.body["participants"][5], req.body["participants"][6], req.body["participants"][7], req.body["participants"][8], req.body["participants"][9]])

    // send data to browser
    res.setHeader('Content-Type', 'application/json');
    // console.log("d:", d)
    js = null
    if(isJsonString(d)) {
        js = JSON.parse(d)
        console.log("successfully loaded json")
    }
    jsn = {"win": 0.25, "status_code": 200}
    console.log("sending response: ", jsn)
    // js.status = 200
    res.send(jsn);
    

    // res.end()
});

app.get("/api/champs", async (req, res, next) => {
    res.send(JSON.stringify({"hi": "hi"}));

    // res.end()
});

app.listen(5000, () => {
    console.log("Server running on port 5000");
});