<?php
    ini_set('display_errors', 1);
    error_reporting(E_ALL);

    session_start();

    unset($_SESSION['userId']);
    unset($_SESSION['notUserId']);

    header("location:./main.phtml");
?>