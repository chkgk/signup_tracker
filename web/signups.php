<?php

// testing only
ini_set('display_errors', 1);
ini_set('display_startup_errors', 1);
error_reporting(E_ALL);
// remove later

require_once('credentials.php');

try {
    $file_db = new PDO($DB_FILE);
    $result = $file_db->query("SELECT * FROM participants_table WHERE id > 2");
    $res_array = [];
    $change_res_array = [];
    $old_count = NULL;
    foreach ($result as $row) {
        $x_val = $row['time'];
        $y_val = $row['count'];
        $res_array[] = [$x_val, $y_val];
        if ($old_count != NULL) {
            $y_change = $row['count'] - $old_count;   
        } else {
            $y_change = 0;
        }
        $change_res_array[] = [$x_val, $y_change];
        $old_count = $row['count'];
    }
} catch (PDOException $e) {
    die($e->getMessage());
}



function get_javascript_string($res_array) {
    $data = "[";
    foreach ($res_array as $element) {
        $data .= "[Date.parse('" . $element[0] . "'), " . $element[1] . "], ";
    }
    $data .= "]";
    return $data;
}


$participant_data = get_javascript_string($res_array);
$change_data = get_javascript_string($change_res_array);

?>
<html>
    <head>
    
    </head>
    <body>
        <div id="container" style="min-width: 800px; max-width: 1024px; height: 600px; margin: 0 auto">
        <script src="highcharts.js"></script>
        <script type="text/javascript">
            Highcharts.chart('container', {
                chart: {
                    type: 'spline'
                },
                title: {
                    text: 'AWI Lab Active Participants since 17 October 2017'
                },
                subtitle: {
                    text: 'Data is collected every 3 hours. All times are in CEST.'
                },
                xAxis: {
                    type: 'datetime',
                    title: {
                        text: 'Date'
                    }
                },
                yAxis: [{
                    title: {
                        text: 'active participants',
                        style: {
                            color: Highcharts.getOptions().colors[1]
                        }
                    },
                    labels: {
                        style: {
                            color: Highcharts.getOptions().colors[1]
                        }
                    }
                },{
                    title: {
                        text: 'change',
                        style: {
                            color: Highcharts.getOptions().colors[0]
                        }
                    },
                    labels: {
                        style: {
                            color: Highcharts.getOptions().colors[0]
                        }
                    },
                    opposite: true,
                    tickInterval: 1
                }],
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

                series: [
                {
                    name: 'change',
                    data: <?php echo $change_data ?>,
                    yAxis: 1,
                    type: 'column'
                },{
                    name: 'active participants',
                    data: <?php echo $participant_data ?>,
                    yAxis: 0,
                    type: 'spline'
                }]
            });
        </script>
    </body>
</html>