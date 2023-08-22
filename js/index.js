const latitudeInput = document.querySelector("#lat");
const longitudeInpt = document.querySelector("#long");

function postToServer() {
    let userLocation = {
        latitude: document.querySelector("#lat").valueAsNumber,
        longitude: document.querySelector("#long").valueAsNumber,
    };
    // latitude = latitudeInput.value;
    // longitude = longitudeInpt.value;
    console.log(userLocation);
}

async function getUserLocation() {
    if (navigator.geolocation) {
        await navigator.geolocation.getCurrentPosition(async (local) => {
            let latitude = await local.coords.latitude;
            let longitude = await local.coords.longitude;
            document.querySelector("#lat").value = latitude;
            document.querySelector("#long").value = longitude;
        });
    }
}

document.getElementById("latlong-form").addEventListener("submit", function(event) {
    event.preventDefault();

    const latitude = document.getElementById("lat").value;
    const longitude = document.getElementById("long").value;

    // Create a JSON object with latitude and longitude
    const data = {
        latitude: latitude,
        longitude: longitude
    };

    fetch('/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.text())
        .then(result => {
            document.getElementById("result").innerHTML = result;
            console.log(result)
        })
        .catch(error => {
            console.error('Error:', error);
        });
});