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

    var d = "";
    const pythonProcess = spawn('python3',["./fill_files.py", req.body["tier"], req.body["participants"][0], req.body["participants"][1], req.body["participants"][2], req.body["participants"][3], req.body["participants"][4], req.body["participants"][5], req.body["participants"][6], req.body["participants"][7], req.body["participants"][8], req.body["participants"][9]]);
    pythonProcess.stdout.on('data', (data) => {
        console.log("GETTING DATA:", data.toString());
        d = d + data.toString();
       });
    pythonProcess.on('close', (code) => {
        console.log(`child process close all stdio with code ${code}`);
        // send data to browser
        res.setHeader('Content-Type', 'application/json');
        console.log("d:", d)
        js = null
        if(isJsonString(d)) {
            js = JSON.parse(d)
        }
        jsn = {"win": 0.25, "status_code": 200}
        console.log("sending response: ", jsn)
        // js.status = 200
        res.send(jsn);
    });

    // res.end()
});

app.get("/api/champs", async (req, res, next) => {
    res.send(JSON.stringify({"hi": "hi"}));

    // res.end()
});

app.listen(5000, () => {
    console.log("Server running on port 5000");
});