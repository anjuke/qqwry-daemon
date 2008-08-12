<?php

$ip = "250.197.214.126";
$location = getLocation($ip);
echo "$ip - $location\n";

function getLocation($ip) {
    $socket = socket_create(AF_UNIX, SOCK_STREAM, 0);
    $ret = socket_connect($socket, "/tmp/qqwry.sock");
    if (!$ret) {
        return "ERROR";
    }
    $ret = socket_write($socket, "$ip\n");
    if (!$ret) {
        return "ERROR";
    }
    $read = socket_read($socket, 1024);
    socket_close($socket);
    return $read;
}

function getMicrotimeFloat()
{
    list($usec, $sec) = explode(" ", microtime());
    return ((float)$usec + (float)$sec);
}

$i = 0;
$time = getMicrotimeFloat();
while (true) {
    $a = rand(0, 255);
    $b = rand(0, 255);
    $c = rand(0, 255);
    $d = rand(0, 255);

    $ip = "$a.$b.$c.$d";
    $location = getLocation($ip);
    $i++;
    $etime = getMicrotimeFloat() - $time;
    $time = getMicrotimeFloat();
    echo "$i - $etime - $ip - $location\n";
}
?>