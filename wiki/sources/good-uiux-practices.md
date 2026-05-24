---
type: source
title: "<iframe src="https://projector.datacamp.com/?auto_play=pause&amp;projector_key=c"
slug: good-uiux-practices
date_ingested: 2026-05-24
original_file: raw/Good UIUX practices.md
tags: []
---

---
title: "Good UI/UX practices"
source: "https://campus.datacamp.com/courses/building-dashboards-with-shinydashboard/adding-design-elements-and-improving-uiux?ex=1"
author:
  - "[[continuing]]"
  - "[[you accept our]]"
published:
created: 2026-04-18
description: "Here is an example of Good UI/UX practices:"
tags:
  - "clippings"
---
<iframe src="https://projector.datacamp.com/?auto_play=pause&amp;projector_key=course_31088_09d0c2339130a1dee4b822c405a806cb&amp;video_hls=https%3A%2F%2Fdatacamp-projector-video-recorder-uploads-prod.s3.amazonaws.com%2Fmp4%2F0e30f9dd-efeb-4681-a0b3-c25ac9aa285e.mp4%3FX-Amz-Algorithm%3DAWS4-HMAC-SHA256%26X-Amz-Credential%3DASIAUMJDGTMHYWLQ3OEF%252F20260418%252Fus-east-1%252Fs3%252Faws4_request%26X-Amz-Date%3D20260418T131426Z%26X-Amz-Expires%3D1200%26X-Amz-Security-Token%3DIQoJb3JpZ2luX2VjECUaCXVzLWVhc3QtMSJHMEUCIQDMRH3RBC8oyT6y2OUBpykQD3MnNRGoKV9noBG7xY3hngIgFVXqkmiSH3yPJSo5%252F0%252FsEf1R7gyL1swcnKOBhYbduHgqmAUI7v%252F%252F%252F%252F%252F%252F%252F%252F%252F%252FARAEGgwzMDEyNTg0MTQ4NjMiDPmL7488tv4RdqjroyrsBHOSJXnrB7zlrLSohSvTu0QAZPhjgO8pRJhaZUECNXbeNhNPalsvO%252FDXduJTugEYGYpLEY4%252BkDEIkE%252FQ5u9HeCS4XjEIfQxdn8N3tBWxpvBmNwWZJHlopFFmTjBCNgdA%252Fybtjv47Diyw%252Bv8nbVLItGsnpR1BOw9wdfWZwW96ka9btuI1WyVTM1AND3JCVkCPpNHnrO9TW2y6Mk6N2banhBl0RZGYfR5pBOGjKfmI68xgSw4%252BXFPXjqdWN7hsUc26SBWBbofYyCMVemPhXPDpYV2FQVBEHvBtpDN6wST8bz9jTQvbGdP3uCPNWeFFY7sw6yu3G6NbV5ozVskpdUFygC5KGZ3z5VyUCAm7eXfxjTWGCgfzNROXXTlcprMN%252FEGhcVAJHAMGZ8y81BHM5YXx08kS9VAX8iq3q2Sg3LXB3ZHCb%252FxDPU9rAwmrBqttzozdfVSgFDQqw0V4xq5zY0lpIfQ4s1r8WD4lzAgSeQa0yAj%252B9I6M7V%252FroL1UUfubgj%252Frs8je10doUxs7wE629xp2bhvrR1QyeDRgm9WUGV%252FxUg43%252BHTI7afBJ%252FGD0KfYZPG77CUJa5aTdsejy3Js2W1JP3psoD75vw%252FgVqJhVPUCZhJJXwIMe7KJBeiFuPDhYCyGXgLDCKZWI0KBNP6SMixOEPoVWEYDetnsM%252FeoyR3A0BO4kR9ecx0ma1JjgYmBEJNQ9R8pYvXkkc91v94gJW2%252FiinTV9QL2%252B8atbbzHfBP7I5UlE5O5UYURT8olXviRyEjsqUrdrlQp0OMJpkq1TYHqP%252Bj5JFAsMvZq7ovQzb%252Ffonx49Lh40oOFtKGSTOPMOT9jc8GOpkBDlADbNLpUSB0D47umzoTeEr2p2Vmm0JURJnmOoPhN6GvBrg6HJixod%252Ftksmr1h21GNXKFAuP9RaL5cIaps6uaYMS3M4vRXMp%252FA8DRU9wVC8fZBj4ZZvBBEK8ZyKmwoWpWYORBf%252Bml0%252BmI7AU9LPRCEsyUa5oSnKAnR%252FUXdjuEBz3jjX3HceX%252FZhl7EJfvLyaR8Lf1aTAZHSr%26X-Amz-Signature%3D046211cae46d27f6774d2e677369a1e9fd6fe985fddd988310caebe57ee416b6%26X-Amz-SignedHeaders%3Dhost" title="Good UI/UX practices"></iframe>

#### 1\. Good UI/UX practices

Let's now run through some good practices when designing a dashboard.

#### 2\. Some principles

Here is a list of some principles that we will discuss. These points apply not only to a shinydashboard but any dashboard in general. The list is by no means exhaustive, nor is it universal, but these points should serve as suggestions to help you get started as you develop your own style. Let's elaborate on each point.

#### 3\. 1. Be clear about the purpose of the dashboard

The first is to understand the purpose of the dashboard. Who is the dashboard for? What do they need to know? A better understanding of user requirements will improve user experience. For instance, we may want to construct a dashboard for a private investment client, called Sally, who invests in stocks. The purpose would be to report the performance of her portfolio.

#### 4\. 2. Choose appropriate visualizations

The second is to choose appropriate visualizations. This pertains to individual visualizations but applies to a dashboard too. After all, a dashboard is a visualization that is made up of many pieces. In our example, what information will be useful to Sally? We can plot a line chart containing trends of stock prices, but there are many more options. As there is always a trade-off between clarity and accuracy of information presented, one ought to be mindful of the purpose and target audience. To find out more, we can look at this chart by Alberto Cairo, from his book titled "The truthful art". He suggests that visualizations ought to be selected for different purposes.

#### 5\. 3. Use colors effectively/intuitively

Next, we ought to use colors effectively. Conventionally, certain colors convey different meanings. For instance, red usually denotes a warning or alert, and users will expect it to be so. Green, on the other hand, usually denotes a success message. Let's look at an example where we have a menuItem. Setting badgeColor to red to denote a positive profit may confuse some users. Green is more appropriate in this case.

#### 6\. 3. Use colors effectively/intuitively

Green will be more appropriate in this case.

#### 7\. 4. Truncate large values

Truncate large values or round off to some number of decimal places. We have seen how numbers can be presented in a shinydashboard. To present the values effectively, we have to sacrifice some precision for clarity. To this end, we ought to round large numbers off. This can be achieved by either using the round function or manually changing the number if it's stored as a string. Compare the two images. Which of these is more readable? The bottom one will be clearer for most!

#### 8\. 5. Avoid too many interactive elements

We should be mindful about the number of interactive elements placed in any dashboard. While having interactive elements makes for a more engaging dashboard, having too many such elements may confuse some users. Remember, more is not always better.

#### 9\. 6. Design the dashboard last

Don't rush into designing the dashboard as a first step. This includes wireframing, aesthetic design and the like. We should first determine the purpose of the dashboard, which in turn helps us choose appropriate visualizations.

#### 10\. 6. Design the dashboard last

In our example, the purpose was to communicate the portfolio performance to Sally. Since her portfolio is made up of several stocks, she may want to see how her portfolio is performing. She may also want to track the performance of individual stocks in her portfolio. Once we are clear about the purpose and the parts required, we can then decide on their placements. Do we put them all on a single page, or do we distribute them across several pages? That's up to you to decide!

#### 11\. Let's practice!

Now let's check your understanding of these principles!
