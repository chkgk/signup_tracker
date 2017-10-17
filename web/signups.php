<?php

// testing only
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
// remove later

require_once('credentials.php');

try {
    $file_db = new PDO($DB_FILE);
    $result = $file_db->query("SELECT * FROM participants_table");
    $res_array = [];
    foreach ($result as $row) {
        $x_val = $row['time'];
        $y_val = $row['count'];
        $res_array[] = [$x_val, $y_val];
    }
} catch (PDOException $e) {
    die($e->getMessage());
}

$data = "[";
foreach ($res_array as $element) {
    $data .= "[Date.parse('" . $element[0] . "'), " . $element[1] . "], ";
}
$data .= "]";



?>
<html>
    <head>
    
    </head>
    <body>
        <div id="container" style="min-width: 800px; max-width: 1024px; height: 400px; margin: 0 auto">
        <script src="highcharts.js"></script>
        <script type="text/javascript">
            Highcharts.chart('container', {
                chart: {
                    type: 'spline'
                },
                title: {
                    text: 'AWI Lab sign-ups since 17 October 2017'
                },
                subtitle: {
                    text: 'Data is collected every 3 hours. All times are in UTC.'
                },
                xAxis: {
                    type: 'datetime',
                    title: {
                        text: 'Date'
                    }
                },
                yAxis: {
                    title: {
                        text: 'Active Participants'
                    },
                    min: 1500
                },
                tooltip: {
                    headerFormat: '<b>{series.name}</b><br>',
                    pointFormat: '{point.x:%e. %b %Y - %H:%M}: {point.y:.0f}'
                },

                plotOptions: {
                    spline: {
                        marker: {
                            enabled: true
                        }
                    }
                },

                series: [{
                    name: 'active participants',
                    data: <?php echo $data ?>
                }]
            });
        </script>
    </body>
</html>