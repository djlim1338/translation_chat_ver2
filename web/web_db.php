<?php
    function conndb(){
        $host = "localhost";
        $username = "djlim";
        $password = "12341324";
        $database = "translation_chat_web";
    
        $condb = mysqli_connect($host, $username, $password, $database);
    
        if (mysqli_connect_errno()) {
            die("MySQL 데이터베이스 연결에 실패했습니다: " . mysqli_connect_error());
            return False;
        }
        return $condb;
    }
?>