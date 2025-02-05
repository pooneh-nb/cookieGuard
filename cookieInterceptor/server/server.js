const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const fs = require('fs');
const jsonfile = require('jsonfile');
const path = require('path');
const app = express();
const port = 3000;

app.use(cors({ credentials: true, origin: true }));
app.use(bodyParser.urlencoded({ limit: '100mb', extended: true }));
app.use(bodyParser.json());


async function insertCookieLogs(logs, visitingDomain) {

    const directoryPath = path.join('output', visitingDomain);
    if (!fs.existsSync(directoryPath)) {
        fs.mkdirSync(directoryPath, { recursive: true });
    }

    const file = path.join(directoryPath, 'cookielogs.json');

    jsonfile.writeFile(file, logs, {
        flag: 'a'
    }, function(err) {
        if (err) console.error(err);
    });
}

app.post('/cookieLogs', (req, res) => {
    if (!req.body.visitingDomain) {
        res.status(400).send("Website identifier is required.");
        return;
    }
    insertCookieLogs(req.body, req.body.visitingDomain);
    res.send("Request logged successfully");
});


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