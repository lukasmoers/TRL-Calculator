/* Roadmap (for About page) */
function showDescription(id) {
	var screen = document.getElementById("screen");
	var number = parseInt(id.split('-')[1]);
	var levels = JSON.parse(levels_string);
	
	var initialRoad = document.getElementById("incomplete-0");
	var roads = document.getElementsByClassName("incomplete");
	var pins = document.getElementsByClassName("step-img");
	var bluePin = document.getElementById("step-img-" + number);
	
	initialRoad.style.filter = "grayscale(0)";
	
	for (var i = 0; i < roads.length; i++) {
		if (i < number - 1) {
			roads[i].style.filter = "grayscale(0)";
			pins[i].style.filter = "grayscale(0.3)";
		} else {
			roads[i].style.filter = "grayscale(1)";
			pins[i].style.filter = "grayscale(1)";
		}
	}
	
	bluePin.style.filter = "grayscale(0)";
	
	screen.innerHTML = `<b>TRL ${number} : ${levels[number - 1]['title']}</b><p>${levels[number - 1]['description']}</p></b>`;
}


/* Tutorial page */
function toggleVideo1(){
  var tutorial1 = document.getElementById("create");
  var video1 = document.getElementById("vid-create");
  tutorial1.classList.toggle("active");
  video1.pause();
  video1.currentTime = 0;
}

function toggleVideo2(){
  var tutorial2 = document.getElementById("update");
  var video2 = document.getElementById("vid-update");
  tutorial2.classList.toggle("active");
  video2.pause();
  video2.currentTime = 0;
}

function toggleVideo3(){
  var tutorial3 = document.getElementById("report");
  var video3 = document.getElementById("vid-report");
  tutorial3.classList.toggle("active");
  video3.pause();
  video3.currentTime = 0;
}


/* Project details pages */
function preventSubmitOnEnter(event) {
    if (event.keyCode === 13) {
		event.preventDefault();
    }
}

function validateProjectName(input) {
	var existingNames = JSON.parse(userProjects.replace(/&quot;/g,'"'));

	if (existingNames.includes(input.value)) {
		input.setCustomValidity("Project name already exists.");
	} else if (input.value.length == 0) {
		input.setCustomValidity("Please fill in this field.");
	} else {
		input.setCustomValidity("");
	}
}

function validateProjectSophiaNumber(input) {
	const regex = /([0-9]{4}-[0-9]{3})( *, *[0-9]{4}-[0-9]{3})*/;
	const trimmedInput = input.value.trim();

	if (regex.test(trimmedInput)) {
		input.setCustomValidity('');
	} else {
		input.setCustomValidity('Only comma-separated sophia numbers accepted (e.g. 1234-567, 7654-321...).');
	}
}

function validateProjectCategory() {
	var options = document.querySelectorAll('input[type=checkbox]');
	var selected = false;
	
	for (i = 0; i < options.length; i++) {
		if (options[i].checked) {
			selected = true;
			break;
		}
	}
	
	if (!selected) {
		options[0].setCustomValidity("Please select at least one option.");
	} else {
		options[0].setCustomValidity("");
	}
}


/* Level requirement pages */
function updatePercent(slider, id) {
	var idClean = id.split('-')[1];
	var percent = document.getElementById('percent-' + idClean);
	percent.value = slider.value;
}

function updateSlider(percent, id) {
	var idClean = id.split('-')[1];
	var slider = document.getElementById('slider-' + idClean);
	slider.value = percent.value;
}

function markComplete(id) {
	var idClean = id.split('-')[1];
	var slider = document.getElementById('slider-' + idClean);
	var percent = document.getElementById('percent-' + idClean);
	slider.value = 100;
	percent.value = 100;
}

function expandComment(button, id) {
	var idClean = id.split('-')[1];
	var comment = document.getElementById('comment-' + idClean);
	var gap =  document.getElementById('gap-' + idClean);
	
	if (comment.style.display === "none") {
		comment.style.display = "block";
		gap.style.display = "block";
		button.title = "Hide comment";
	} else {
		comment.style.display = "none";
		gap.style.display = "none";
		if (comment.value == "") { 
			button.title = "Add comment";
		} else {
			button.title = "Edit comment";
		}
	}
}

function editComment(comment, id) {
	var idClean = id.split('-')[1];
	var button = document.getElementById('bubble-' + idClean);
	
	if (comment.value == "") { 
		button.style.backgroundColor = "#F6F6F8";
	} else {
		button.style.backgroundColor = "#80bf70";
	}
}


/* Project overview page */
function activateFields(version) {
	var fromLevel = document.querySelector("select[name='from_level']");
	var toLevel = document.querySelector("select[name='to_level']");
	var comments = document.querySelectorAll("input[name='comments']");
	
	if (version.id == "id_version_0") {
		fromLevel.disabled = true;
		toLevel.disabled = true;
		comments[0].disabled = true;
		comments[1].disabled = true;
		
		fromLevel.title = "Extended version only";
		toLevel.title = "Extended version only";
		comments[0].title = "Extended version only";
		comments[1].title = "Extended version only";

		fromLevel.required = false;
		toLevel.required = false;
		comments[0].required = false;
		comments[1].required = false;
	} else {
		fromLevel.disabled = false;
		toLevel.disabled = false;
		comments[0].disabled = false;
		comments[1].disabled = false;
		
		fromLevel.title = "Select from which level";
		toLevel.title = "Select up to which level";
		comments[0].title = "Include comments";
		comments[1].title = "Don't include comments";

		fromLevel.required = true;
		toLevel.required = true;
		comments[0].required = true;
		comments[1].required = true;
	}
}


/* Local login/register pages */
function resetError() {
	var error = document.getElementById("login-error");
	error.innerHTML = "";
}