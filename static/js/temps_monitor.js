/**
 * Build an array of annotations from an array of timestamps.
 *
 * @param  timestamp  A timestamp of the form "Sun Oct 17  03:12:47".
 */
function build_annotations(timestamps)
{
	var annotations = [];
	var length = timestamps.length;

	for (let i = 0; i < length; i++)
	{
		var ts = timestamps[i];

		// Skip if not time to create an annotation
		if (!is_annotation_time(ts))
		{
			continue;
		}

		// Create an annotation
		var a = {
			type: "line",
			scaleId: "x",
			borderWidth: 1,
			borderColor: "#777777",
			xMin: i,
			xMax: i,
			label: {
				backgroundColor: "#777777",
				enabled: true,
				content: timestamp_24h_to_12h_abbr(ts),
				position: "start"
			},
		};

		// Store all created annotations
		annotations.push(a);
	}

	return annotations;
}

/**
 * Build the object that defines the data on the plot.
 */
function build_plot_data(timestamps, temps, color)
{
	setup_plot_timestamps(timestamps);

	return {
			labels: timestamps,
			datasets: [
				{
					data: temps,
					borderColor: color,
					fill: true,
					lineTension: 0.4
				}
			]
	};
}

/**
 * Build the object that defines that options and annotations that will be
 * drawn on the plot.
 */
function build_plot_options(title, annotations)
{
	return {
		response: true,
		plugins: {
			annotation: {
				annotations: annotations
			},

			legend: {
				display: false
			},

			title: {
				display: true,
				text: title,
				font: {
					size: 20,
					weight: "bold"
				}
			},

			tooltip: {
				mode: "index",
				intersect: "false",
				callbacks: {
					title: function(items) {
						var chart = items[0].chart;
						var timestamps = chart.config._config.data.labels;
						var label = items[0].label;
						var index = items[0].dataIndex;

						// Find the date, since the current label will often just be the time
						for (let i=index; i >= 0; i--)
						{
							// An array indicates a date label, whereas a string is a time label
							if (timestamps[i].constructor == Array)
							{
								// The current label was actually a date all along
								if (i == index)
								{
									label = timestamps[i][1];
								}

								// Display the date in front of the time
								return timestamps[i][0] + "  @  " + label;
							}
						}

						// Should never get here, but return the default label for safety
						return label;
					},

					label: function(item) {
						var value = item.formattedValue;

						// Add the units to the temp, as well as some space
						return "  " + value + " °C";
					}
				}
			}
		},

		scales: {
			x: {
				//type: "time",
				ticks: {
					display: true,
					includeBounds: true,
					maxRotation: 0
				},

				title: {
					display: true,
					text: "Time",
					font: {
						size: 16,
						weight: "bold"
					}
				}
			},

			y: {
				title: {
					display: true,
					text: "Temp (C)",
					font: {
						size: 16,
						weight: "bold"
					}
				}
			}
		}
	};
}

/**
 * Get the frequency at which to clear the timestamp label. This number will be
 * modded, "%", against the minutes value to determine if the label should be
 * cleared or not.
 *
 * @param  length  The length of the timestamps array.
 */
function get_clear_timestamp_frequency(length)
{
	console.log("Length : " + length);
	day1 = 1440 / 5;
	day2 = day1 * 2;
	day3 = day1 * 3;

	if (length <= day1)
	{
		return 15;
	}
	else if (length <= day2)
	{
		return 30;
	}
	else if (length <= day3)
	{
		return 0;
	}
	else
	{
		return 0;
	}
}

/**
 * Get the date from a timestamp.
 *
 * @param  timestamp  A timestamp of the form "Sun Oct 17  03:12:47".
 */
function get_date_from_timestamp(timestamp)
{
	return timestamp.substring(0, 10);
}

/**
 * Get the time from a timestamp.
 *
 * @param  timestamp  A timestamp of the form "Sun Oct 17  03:12:47".
 */
function get_time_from_timestamp(timestamp)
{
	return timestamp.substring(12, 17);
}

/**
 * Check if a time corresponds to one in each an annotation should be on. An
 * annotation will only be created on these times, below:
 *
 * 00:00
 * 06:00
 * 12:00
 * 18:00
 *
 * @param  timestamp  A timestamp of the form "Sun Oct 17  03:12:47".
 */
function is_annotation_time(timestamp)
{
	var time = get_time_from_timestamp(timestamp);

	return ((time.localeCompare("00:00") == 0) || 
		(time.localeCompare("06:00") == 0) ||
		(time.localeCompare("12:00") == 0) ||
		(time.localeCompare("18:00") == 0));
}

/**
 * Setup timestamps for the plot, so that they can be displayed more easily in
 * the browser.
 *
 * @param  timestamp  A timestamp of the form "Sun Oct 17  03:12:47".
 */
function setup_plot_timestamps(timestamps)
{
	var prev = "";
	var length = timestamps.length;

	for (let i = 0; i < length; i++)
	{
		var ts = timestamps[i];
		var current = get_date_from_timestamp(ts);
		var time = get_time_from_timestamp(ts);

		// Clear label depending on how much data is going to be shown
		//if (!should_show_timestamp_label(time, length))
		//{
		//	timestamps[i] = "";
		//}

		// On a new date, put the timestamp on two lines
		//else if (!prev || current.localeCompare(prev) != 0)
		if (!prev || current.localeCompare(prev) != 0)
		{
			timestamps[i] = [current, time];
			prev = current;
		}

		// On the same date, just use the hour
		else
		{
			timestamps[i] = time;
			prev = current;
		}

	}

	return timestamps;
}

/**
 * Whether to clear the timestamp label or not.
 */
function should_show_timestamp_label(time, length)
{
	var hour = parseInt(time.substring(0, 2));
	var minute = parseInt(time.substring(3, 5));

	var day1 = 1440 / 5;
	var day2 = day1 * 2;
	var day3 = day1 * 3;

	if (length <= day1)
	{
		//return ((minute % 15) == 0);
		return ((minute % 30) == 0);
	}
	else if (length <= day2)
	{
		//return ((minute % 30) == 0);
		return (((hour % 1) == 0) && (minute == 0));
	}
	else if (length <= day3)
	{
		return (((hour % 2) == 0) && (minute == 0));
	}
	else
	{
		return (((hour % 4) == 0) && (minute == 0));
	}
}

/**
 * Convert a 24h timestamp, e.g. Sat Oct 16  13:10, to a 12h abbreviated verion,
 * which cuts out everything except the hour and the meridian, e.g. 1pm.
 *
 * @param  timestamp  A timestamp of the form "Sun Oct 17  03:12:47".
 */
function timestamp_24h_to_12h_abbr(timestamp)
{
	var time = get_time_from_timestamp(timestamp);
	var hour = parseInt(time.substring(0, 2));
	var meridian = (hour < 12) ? "AM" : "PM";

	if (hour == 0)
	{
		hour = 12;
	}
	if (hour == 18)
	{
		hour = 6;
	}

	return hour.toString() + " " + meridian;
}
