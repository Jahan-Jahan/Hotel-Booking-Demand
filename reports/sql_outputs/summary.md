# SQL Analytical Results

## q1_cancel_by_month

- **Insight:** Cancellation rates peak during spring and early summer (highest in June at 41.46% and April at 40.80%) compared to winter months (lowest in January at 30.48%).

|   arrival_month_num | arrival_date_month   |   total_bookings |   canceled_bookings |   cancellation_rate_pct |
|--------------------:|:---------------------|-----------------:|--------------------:|------------------------:|
|                   1 | January              |             5929 |                1807 |                   30.48 |
|                   2 | February             |             8068 |                2696 |                   33.42 |
|                   3 | March                |             9794 |                3149 |                   32.15 |
|                   4 | April                |            11089 |                4524 |                   40.8  |
|                   5 | May                  |            11791 |                4677 |                   39.67 |
|                   6 | June                 |            10939 |                4535 |                   41.46 |
|                   7 | July                 |            12661 |                4742 |                   37.45 |
|                   8 | August               |            13877 |                5239 |                   37.75 |
|                   9 | September            |            10508 |                4116 |                   39.17 |
|                  10 | October              |            11160 |                4246 |                   38.05 |
|                  11 | November             |             6794 |                2122 |                   31.23 |
|                  12 | December             |             6780 |                2371 |                   34.97 |

## q2_cancel_by_lead_time

- **Insight:** Cancellation rate increases monotonically with lead time, rising from 9.63% for bookings made 0-7 days in advance to 57.01% for bookings made 181+ days ahead.

| lead_time_bucket   |   bucket_order |   total_bookings |   canceled_bookings |   cancellation_rate_pct |
|:-------------------|---------------:|-----------------:|--------------------:|------------------------:|
| 00-07 days         |              1 |            19746 |                1902 |                    9.63 |
| 08-30 days         |              2 |            18960 |                5283 |                   27.86 |
| 31-90 days         |              3 |            29553 |               11141 |                   37.7  |
| 91-180 days        |              4 |            26439 |               11821 |                   44.71 |
| 181+ days          |              5 |            24692 |               14077 |                   57.01 |

## q3_adr_by_market_segment

- **Insight:** Online TA (117.96) and Direct (117.69) generate the highest average positive ADR, whereas Corporate (70.45) and Complementary (34.04) sit at the lower end.

| market_segment   |   total_bookings |   positive_adr_bookings |   avg_adr_positive_only |   avg_adr_all_rows |
|:-----------------|-----------------:|------------------------:|------------------------:|-------------------:|
| Online TA        |            56477 |                   56110 |                  117.96 |             117.2  |
| Direct           |            12606 |                   12366 |                  117.69 |             115.45 |
| Aviation         |              237 |                     231 |                  102.74 |             100.14 |
| Offline TA/TO    |            24219 |                   23887 |                   88.57 |              87.35 |
| Groups           |            19811 |                   19558 |                   80.51 |              79.48 |
| Corporate        |             5295 |                    5213 |                   70.45 |              69.36 |
| Complementary    |              743 |                      63 |                   34.04 |               2.89 |
| Undefined        |                2 |                       2 |                   15    |              15    |

## q4_cumulative_bookings

- **Insight:** Cumulative arrival bookings grow steadily over time using a running window sum, tracking total booking volume accumulated up to each arrival date.

| arrival_day   |   bookings_count |   cumulative_bookings |
|:--------------|-----------------:|----------------------:|
| 2015-07-01    |              122 |                   122 |
| 2015-07-02    |               93 |                   215 |
| 2015-07-03    |               56 |                   271 |
| 2015-07-04    |               88 |                   359 |
| 2015-07-05    |               53 |                   412 |
| 2015-07-06    |               75 |                   487 |
| 2015-07-07    |               54 |                   541 |
| 2015-07-08    |               69 |                   610 |
| 2015-07-09    |               80 |                   690 |
| 2015-07-10    |               51 |                   741 |
| 2015-07-11    |              103 |                   844 |
| 2015-07-12    |               63 |                   907 |

## q5_mom_cancel_rate_lag

- **Insight:** Using LAG reveals sharp month-over-month shifts in cancellation rate, such as a -14.17 percentage point drop in November 2015 followed by a +12.55 percentage point rebound in December 2015.

|   arrival_date_year |   arrival_month_num |   total_bookings |   cancel_rate_pct |   prev_month_cancel_rate_pct |   mom_cancel_rate_diff_pp |
|--------------------:|--------------------:|-----------------:|------------------:|-----------------------------:|--------------------------:|
|                2015 |                   7 |             2776 |             45.35 |                       nan    |                    nan    |
|                2015 |                   8 |             3889 |             41.09 |                        45.35 |                     -4.26 |
|                2015 |                   9 |             5114 |             40.95 |                        41.09 |                     -0.14 |
|                2015 |                  10 |             4957 |             34.94 |                        40.95 |                     -6.01 |
|                2015 |                  11 |             2340 |             20.77 |                        34.94 |                    -14.17 |
|                2015 |                  12 |             2920 |             33.32 |                        20.77 |                     12.55 |
|                2016 |                   1 |             2248 |             24.78 |                        33.32 |                     -8.54 |
|                2016 |                   2 |             3891 |             34.36 |                        24.78 |                      9.58 |
|                2016 |                   3 |             4824 |             30.62 |                        34.36 |                     -3.74 |
|                2016 |                   4 |             5428 |             37.97 |                        30.62 |                      7.35 |
|                2016 |                   5 |             5478 |             34.96 |                        37.97 |                     -3.01 |
|                2016 |                   6 |             5292 |             39.61 |                        34.96 |                      4.65 |
