function validateSignupForm() {
    var n = document.forms["signup_form"]["name"].value;
    var x = document.forms["signup_form"]["email"].value;
    var atpos = x.indexOf("@");
    var dotpos = x.lastIndexOf(".");
    var y = document.forms["signup_form"]["password"].value;
    var z = document.forms["signup_form"]["verifyPassword"].value;

    if (w == null || w == "") {
        alert("Please enter your full name.");
        return false;
    }
    if (x == null || x == "") {
        alert("Please enter your email address.");
        return false;
    }
    if (atpos< 1 || dotpos<atpos+2 || dotpos+2>=x.length) {
        alert("Not a valid email address.");
        return false;
    }
    if (y == null || y == "") {
        alert("Please fill the password field.");
        return false;
    }
    if (z != y) {
        alert("Passwords do not match.");
        return false;
    }
}

function validateLoginForm() {
    var x = document.forms["login_form"]["email"].value;
    var atpos = x.indexOf("@");
    var dotpos = x.lastIndexOf(".");
    var y = document.forms["login_form"]["password"].value;

    if (x == null || x == "") {
        alert("Please enter your email address!");
        return false;
    }
    if (atpos< 1 || dotpos<atpos+2 || dotpos+2>=x.length) {
        alert("Not a valid email address.");
        return false;
    }
    if (y == null || y == "") {
        alert("Please fill the password field.");
        return false;
    }
}

function validateLogin () {
    var x = document.forms["login_form"]["email"].value;
    var y = document.forms["login_form"]["pass"].value;
    
    if (x == "anuragmathur1311@gmail.com" && y =="abcd1234") {
        return;
    } else if (x == "anuragmathur1311@gmail.com" && y !="abcd1234") {
        alert("Password Incorrect");
        return false;
    } else if (x != "anuragmathur1311@gmail.com" && y =="abcd1234") {
        alert("Username Incorrect");
        return false;
    } else {
        alert("Username and Password Incorrect");
        return false;
    }
}