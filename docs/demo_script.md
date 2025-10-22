# ChatMRPT Demo Script

## THE HOOK (30-45 seconds)

**[Start with energy and a smile]**

In global health, we’re often asked to make critical decisions with limited time, limited resources, and sometimes, limited clarity.

The data isn’t always clean. The stakes are always high. And yet, the expectations keep rising.

That’s the challenge we face — and it's why smarter, more accessible tools matter more than ever.

And that's exactly why I'm here today."

## THE PROBLEM (45 seconds)

In many parts of Nigeria — and across Africa — malaria program officers are making critical decisions without the data they truly need.

Often, the information just isn’t there:

No recent data on high-risk settlements

Incomplete environmental and demographic records

And limited tools to turn what little data exists into something useful

Meanwhile, the question still stands: 'Where should these bed nets go?'

The usual answer? Hire consultants, wait months, and hope the results are still relevant by the time they arrive."


## THE SOLUTION INTRO (30 seconds)

"What if I told you that in a matter of minutes, you could go from raw data, no data to actionable insights? What if you could have a conversation with your data? 

Ladies and gentlemen, meet ChatMRPT - your AI-powered malaria risk prioritization copilot."

## DEMO WALKTHROUGH

### Part 1: The Interface (1 minute)

"Look at this interface. Clean. Simple. Just like texting.

No complicated dashboards. No 47 buttons you'll never use. Just you, having a conversation about your data.

We designed this after several meetings with our partners and stakeholder after the more traditional tools proved difficult to use. Every feature here? It came from someone in the field saying 'I wish I could just...'"

### Part 2: Two Pathways (2 minutes)

"Now here's where it gets exciting. ChatMRPT works TWO ways:

**Option 1**: You've got your data ready? Great! Upload your CSV with demographic and environmental factors, add your shapefile with ward boundaries, and watch the magic happen.

**Option 2**: But wait - you're thinking 'I don't have environmental data!' No problem! You know what you DO have? Your TPR data - your test positivity rates. That's ALL you need. 

ChatMRPT has a built-in database that automatically pulls:
- Rainfall patterns
- Temperature data  
- Population density
- Settlement types
- Everything else you need

Just bring your TPR data, and we'll handle the rest. How's that for making your life easier?"

### Part 3: The Complete Analysis Journey (4-5 minutes)

"Alright, let me walk you through a real analysis...

*[Upload TPR file]*

So I'm uploading our test positivity rate data - this is from actual health facilities. 

*[While file uploads - 45 seconds of engaging content]*

Now while this uploads, let me tell you what's happening behind the scenes. This single Excel file contains data from over 2,600 health facilities - that's millions of test results. Traditional systems would crash just trying to open this.

But ChatMRPT? It's already parsing every row, validating facility codes, checking data quality across all 36 months. It's identifying patterns, flagging anomalies, cross-referencing geographic codes - all automatically.

Think about this - right now, as we wait, ChatMRPT is doing the work of an entire analytics team. It's checking every single ward against the national database, validating that facilities actually exist, ensuring the data makes epidemiological sense.

*[Check upload progress]*

Almost there... And here's what really matters - in about 10 seconds, you'll have insights that are not just fast, but accurate. Because speed without accuracy is just fast failure. ChatMRPT gives you both.

*[Upload completes]*

And... there we go! Look at that - ChatMRPT instantly recognizes everything - states, LGAs, wards, even tells me I have 36 months of data from over 2,600 facilities.

Now it's asking me which state to focus on. I'll select one... and look, it's recommending I use primary health facilities. Why? Because it knows they represent 96% of the data and reflect true community transmission. That's intelligence, not just processing.

*[Make selections]*

Primary facilities, under-5 age group... and done! TPR calculated for all 226 wards. Average is 72.3% - that's high. But now comes the interesting part...

*[Show the transition]*

Now watch this seamless transition - ChatMRPT just gave me three download options. See that? TPR Analysis CSV, but also a 'Complete Analysis CSV' and a shapefile. Here's what just happened behind the scenes:

ChatMRPT took my TPR data and automatically matched it with our comprehensive environmental database according to the geopolitical zone the state's in. It pulled rainfall patterns, temperature data, vegetation indices, elevation, population density - everything that affects malaria transmission. All matched perfectly to each ward.

And the shapefile? ChatMRPT extracted the official ward boundaries from our national geographic database. No more hunting for shapefiles. It's all there, ready for analysis.

*[Click to proceed to risk analysis]*

So now I'm working with enriched data - my TPR results PLUS all the environmental factors that drive transmission. This is why we can do sophisticated risk analysis. We're not just looking at test results in isolation - we're seeing the complete picture.

*[Type naturally while talking]*

Let me ask: 'Tell me about the variables in my data'

See that? It's not just listing them - it's explaining why each one matters. EVI shows vegetation where mosquitoes breed. Housing quality affects exposure. This is what I mean by conversational intelligence.

Actually, let me see this visually...

*[Type: "Plot me the map distribution for the evi variable"]*

There we go! Look at those dark green patches - those are your mosquito hotels right there. And I didn't need any GIS training to create this map. Just asked for it.

Now for the real power...

*[Type: "Run the malaria risk analysis"]*

This is my favorite part. Watch what happens... ChatMRPT immediately shows it's running TWO different analytical methods:

**Composite Score Method** - This is beautifully simple. It takes all your indicators - TPR, housing quality, vegetation, rainfall - normalizes them to a 0-100 scale, and calculates the average. But here's the clever part: it creates multiple models using different combinations of variables and takes the median score. So it's not just one calculation - it's testing your data from multiple angles.

**PCA Method** - Principal Component Analysis. This is the sophisticated approach. Instead of treating all variables equally, PCA finds hidden patterns. Maybe high rainfall areas also have dense vegetation and poor housing - PCA discovers these relationships automatically and weights them accordingly. It can tell you "these 3 factors explain 75% of your malaria risk patterns."

Look at the progress bar... 10 seconds! That's it! Both methods running simultaneously, creating rankings, calculating variable importance, generating risk categories. And here's why we run both: if the simple composite method and the sophisticated PCA method BOTH flag the same wards as high-risk, you have rock-solid evidence for your interventions.

But numbers are just numbers. Let me show you what this means...

*[Type: "Show me the vulnerability map"]*

Now THIS is what you need to see. Red areas - those are your crisis zones. Multiple risk factors all coming together. so we know where the problems are. What do we do about it?

*[Type: "I want to plan bed net distribution"]*

ChatMRPT's asking me two simple questions - how many nets do I have? What's the average household size? I'll say 2 million nets, household size of 4.

*[Enter values]*

And... there's your distribution plan. It's prioritized the highest-risk wards first, calculated exact quantities, ensured 100% coverage where it matters most. No politics, no guesswork - just data-driven allocation that saves lives.

*[Click export]*

And with one click, I get everything - interactive dashboard, detailed spreadsheets, maps for the field teams, executive summary for the directors. 

Start to finish? Under 10 minutes. That's not just efficiency - that's transformation."

### Part 4: The Results (2 minutes)

"But here's where ChatMRPT really shines - the outputs:

1. **Risk Rankings**: Every ward, ranked by malaria risk. Clear priorities.
2. **Interactive Maps**: Click any area, get instant insights
3. **Distribution Plans**: Optimal bed net allocation based on YOUR budget
4. **Downloadable Reports**: Professional reports, ready for your directors

And the best part? This entire analysis that would take weeks? We just did it in minutes."

## THE VALUE PROPOSITION (1 minute)

"Let's talk ROI for a second:

- Traditional consultant: $50,000, 3 months
- ChatMRPT: Fraction of the cost, results in minutes
- More importantly: YOUR team becomes the experts

This isn't about replacing people - it's about empowering them. Your field officers can now do PhD-level analysis. Your data becomes your strategic advantage."

## INTERACTIVE MOMENT (1 minute)

"Now, I want you to imagine something...

What if every malaria program in Nigeria could identify their top 20% highest-risk areas with 90% accuracy? What if we could ensure that EVERY bed net goes exactly where it's needed most?

That's not a dream - that's what users are doing with ChatMRPT right now."

## THE CLOSE (1 minute)

"Listen, I've shown you a tool, but what I'm really offering is transformation. The ability to:
- Make data-driven decisions with confidence
- Justify every dollar spent to donors
- Save lives more efficiently than ever before

ChatMRPT isn't just software - it's your partner in the fight against malaria.

So here's my question: Are you ready to work smarter, not harder? Are you ready to turn your data into your superpower?

Let me show you exactly how ChatMRPT can transform YOUR program..."

## Q&A PREPARATION

**Anticipated Questions:**

1. **"What if our data is really messy?"**
   "That's exactly why we built ChatMRPT! It handles missing data, identifies quality issues, and guides you through cleaning - all conversationally."

2. **"Do we need training?"**
   "If you can use WhatsApp, you can use ChatMRPT. But yes, we provide training and ongoing support."

3. **"How accurate are the predictions?"**
   "Our composite scoring and PCA methods are peer-reviewed and field-tested. We're transparent about confidence levels."

4. **"What about data security?"**
   "Bank-level encryption, local data processing options, and full compliance with health data regulations."

## DEMO TIPS

1. **Energy**: Keep it high but professional
2. **Pace**: Pause for effect, let key points sink in
3. **Engagement**: Make eye contact, ask rhetorical questions
4. **Flexibility**: Read the room, adjust detail level as needed
5. **Confidence**: You're not just showing software, you're offering transformation

Remember: You're not selling a tool - you're selling better health outcomes, smarter resource allocation, and empowered teams. ChatMRPT is just the vehicle to get there.

---

*Practice this 3-5 times before the demo. Time yourself. Get comfortable with the flow. You've got this!*