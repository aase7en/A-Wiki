---
type: source
title: "Good UI/UX practices"
slug: good-uiux-practices
date_ingested: 2026-05-24
original_file: raw/Good UIUX practices.md
---

```yaml
---
title: "Good UI/UX practices"
source: "https://campus.datacamp.com/courses/building-dashboards-with-shinydashboard/adding-design-elements-and-improving-uiux?ex=1"
author: ""
published: ""
created: "2026-04-18"
description: "Here is an example of Good UI/UX practices:"
tags: ""
---
```

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
