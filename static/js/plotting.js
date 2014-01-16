function plot_1d(raw_data, log_scale) {
	log_scale = (typeof log_scale === "undefined") ? false : log_scale;
	
	var data = [];
	for (var i=0; i<raw_data.length; i++) {
		
		if (raw_data[i].y>0 && raw_data[i].dy<raw_data[i].y) {  data.push(raw_data[i]); };
	}
	
    var margin = {top: 20, right: 20, bottom: 40, left: 60},
    width = 500 - margin.left - margin.right,
    height = 300 - margin.top - margin.bottom;

    var x = d3.scale.linear().range([0, width]);
    var y = log_scale ? d3.scale.log().range([height, 0]) : d3.scale.linear().range([height, 0]);
    x.domain(d3.extent(data, function(d) { return d.x; }));
    y.domain(d3.extent(data, function(d) { return d.y; }));

    var xAxis = d3.svg.axis().scale(x).orient("bottom");
    var yAxis = d3.svg.axis().scale(y).orient("left");    
    
    var svg = d3.select("plot_anchor").append("svg")
      .attr("class", "default_1d")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    svg.append("g").attr("class", "x axis").attr("transform", "translate(0," + height + ")").call(xAxis);
    svg.append("g").attr("class", "y axis").call(yAxis)
    
    // Create X axis label   
    svg.append("text")
    .attr("x", width )
    .attr("y",  height+margin.top+15)
    .attr("font-size", "12px")
    .style("text-anchor", "end")
    .text("Q [1/\u00C5]");

    // Create Y axis label
    svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 0-margin.left)
    .attr("x", 0-margin.top)
    .attr("dy", "1em")
    .style("text-anchor", "end")
    .text("Intensity");
    
    // Plot the points
    svg.selectAll('circle')
      .data(data)
      .enter()
      .append('circle')
      .attr("cx", function(d) { return x(d.x); })
      .attr("cy", function(d) { return y(d.y); })
      .attr("r", 2);

    // Error bars
    svg.selectAll('line')
      .data(data)
      .enter()
      .append('line')
    .attr("x1", function(d) { return x(d.x); })
    .attr("y1", function(d) { return y(d.y-d.dy); })
    .attr("x2", function(d) { return x(d.x); })
    .attr("y2", function(d) { return y(d.y+d.dy); });

    svg.append("a")
    .attr("href", 'javascript:void(0);')
    .attr("onClick", 'plot_1d(\"data\");')
    .text("log"); 

}

function plot_2d(data, qx, qy, max_iq) {
    var margin = {top: 20, right: 20, bottom: 40, left: 60},
    width = 300 + margin.left + margin.right,
    height = 300 + margin.top + margin.bottom;

    var x = d3.scale.linear().range([0, width]);
    var y = d3.scale.linear().range([height, 0]);
    x.domain(d3.extent(qx, function(d) { return d; }));
    y.domain(d3.extent(qy, function(d) { return d; }));

    var xAxis = d3.svg.axis().scale(x).orient("bottom");
    var yAxis = d3.svg.axis().scale(y).orient("left");    
    
    var svg = d3.select("plot_anchor_2d").append("svg")
      .attr("class", "Spectral")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    
    var pixel_h = y(qy[0])-y(qy[1]);
    var pixel_w = x(qx[1])-x(qx[0]);
    
    var quantize = d3.scale.quantize()
    .domain([0.,max_iq])
    .range(d3.range(11).map(function(i) { return "q" + i + "-11"; }));
    
    var color = d3.scale.linear()
    .domain([0, max_iq])
    .range(["white", "steelblue"])
    .interpolate(d3.interpolateLab);
    
    svg.selectAll('g')
    .data(data)
    .enter()
    .append('g')
    .attr("transform", function(d,i) { var trans = y(qy[i])-pixel_h; return "translate(0,"+ trans + ")"; })
    .selectAll('rect')
    .data(function(d) { return d; })
    .enter()
    .append('rect')
    .attr('x', function(d,i) { return x( qx[i] ); })
    .attr('y', function(d,i) { return 0; })
    .attr('width', function(d,i) { return pixel_w; })
    .attr('height', function(d,i) { return pixel_h; })
    .attr("class", function(d) { return quantize(d); })
    //.style("fill", function(d) { return color(d); });
    svg.append("g").attr("class", "x axis").attr("transform", "translate(0," + height + ")").call(xAxis);
    svg.append("g").attr("class", "y axis").call(yAxis)

}