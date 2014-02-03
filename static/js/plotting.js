function plot_1d(raw_data, options) {
    options = (typeof options === "undefined") ? {} : options;
    color = (typeof options.color === "undefined") ? '#0077cc' : options.color;
    marker_size = (typeof options.marker_size === "undefined") ? 2 : options.marker_size;
    height = (typeof options.height === "undefined") ? 250 : options.height;
    width = (typeof options.width === "undefined") ? 500 : options.width;
    log_scale = (typeof options.log_scale === "undefined") ? false : options.log_scale;
    x_label = (typeof options.x_label === "undefined") ? "Q [1/\u00C5]" : options.x_label;
    y_label = (typeof options.y_label === "undefined") ? "Intensity" : options.y_label;

    var data = [];
    for (var i=0; i<raw_data.length; i++) {
        if (raw_data[i][1]>0 && raw_data[i][2]<raw_data[i][1]) {  data.push(raw_data[i]); };
    }

    var margin = {top: 20, right: 20, bottom: 40, left: 60},
    width = width - margin.left - margin.right,
    height = height - margin.top - margin.bottom;

    var x = d3.scale.linear().range([0, width]);
    var y = log_scale ? d3.scale.log().range([height, 0]) : d3.scale.linear().range([height, 0]);
    x.domain(d3.extent(data, function(d) { return d[0]; }));
    y.domain(d3.extent(data, function(d) { return d[1]; }));

    var xAxis = d3.svg.axis().scale(x).orient("bottom").ticks(5).tickFormat(d3.format("5.2g"));
    var xAxisMinor = d3.svg.axis().scale(x).orient("bottom").ticks(5).tickSize(3,3).tickSubdivide(5).tickFormat('');
    var yAxis = d3.svg.axis().scale(y).orient("left").ticks(5).tickFormat(d3.format("5.2g"));    
    var yAxisMinor = d3.svg.axis().scale(y).orient("left").ticks(5).tickSize(3,3).tickSubdivide(5).tickFormat('');
    
    // Remove old plot
    d3.select("plot_anchor").select("svg").remove();
    
    var svg = d3.select("plot_anchor").append("svg")
      .attr("class", "default_1d")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    svg.append("g").attr("class", "x axis").attr("transform", "translate(0," + height + ")").call(xAxis);
    svg.append("g").attr("class", "x axis").attr("transform", "translate(0," + height + ")").call(xAxisMinor);
    svg.append("g").attr("class", "y axis").call(yAxis)
    svg.append("g").attr("class", "y axis").call(yAxisMinor)
    
    // Create X axis label   
    svg.append("text")
    .attr("x", width )
    .attr("y",  height+margin.top+15)
    .attr("font-size", "12px")
    .style("text-anchor", "end")
    .text(x_label);

    // Create Y axis label
    svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 0-margin.left)
    .attr("x", 0-margin.top)
    .attr("dy", "1em")
    .style("text-anchor", "end")
    .text(y_label);

    // Plot the points
    svg.selectAll('circle')
      .data(data)
      .enter()
      .append('circle')
      .attr("cx", function(d) { return x(d[0]); })
      .attr("cy", function(d) { return y(d[1]); })
      .attr("r", marker_size)
      .style('fill', color);

    // Error bars
    svg.selectAll('line')
      .data(data)
      .enter()
      .append('line')
    .attr("x1", function(d) { return x(d[0]); })
    .attr("y1", function(d) { return y(d[1]-d[2]); })
    .attr("x2", function(d) { return x(d[0]); })
    .attr("y2", function(d) { return y(d[1]+d[2]); })
    .style('stroke', color)
    .style('stroke-width', marker_size);
}

function plot_2d(data, qx, qy, max_iq, options) {
    options = (typeof options === "undefined") ? {} : options;
    height = (typeof options.height === "undefined") ? 400 : options.height;
    width = (typeof options.width === "undefined") ? 400 : options.width;
    log_scale = (typeof options.log_scale === "undefined") ? false : options.log_scale;
    x_label = (typeof options.x_label === "undefined") ? "Qx [1/\u00C5]" : options.x_label;
    y_label = (typeof options.y_label === "undefined") ? "Qy [1/\u00C5]" : options.y_label;

    var margin = {top: 20, right: 20, bottom: 60, left: 60},
    width = width - margin.left - margin.right,
    height = height - margin.top - margin.bottom;

    var x = d3.scale.linear().range([0, width]);
    var y = d3.scale.linear().range([height, 0]);
    x.domain(d3.extent(qx, function(d) { return d; }));
    y.domain(d3.extent(qy, function(d) { return d; }));

    var xAxis = d3.svg.axis().scale(x).orient("bottom");
    var yAxis = d3.svg.axis().scale(y).orient("left");

    // Remove old plot
    d3.select("plot_anchor_2d").select("svg").remove();
    var svg = d3.select("plot_anchor_2d").append("svg")
      .attr("class", "Spectral")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    var pixel_h = y(qy[0])-y(qy[1]);
    var pixel_w = x(qx[1])-x(qx[0]);

    var quantize;
    if (log_scale) {
      var step = Math.log(max_iq+1.0)/10;
      bins = [0, Math.exp(step)-1.0, Math.exp(2.0*step)-1.0, Math.exp(3.0*step)-1.0,
              Math.exp(4.0*step)-1.0, Math.exp(5.0*step)-1.0, Math.exp(6.0*step)-1.0,
              Math.exp(7.0*step)-1.0, Math.exp(8.0*step)-1.0, Math.exp(9.0*step)-1.0];
      quantize = d3.scale.threshold()
      .domain(bins)
      .range(d3.range(11).map(function(i) { return "q" + i + "-11"; }));
    } else {
        var quantize = d3.scale.quantize()
        .domain([0.,max_iq])
        .range(d3.range(11).map(function(i) { return "q" + i + "-11"; }));
    };

    // Create X axis label   
    svg.append("text")
    .attr("x", width )
    .attr("y", height+margin.top+15)
    .attr("font-size", "12px")
    .style("text-anchor", "end")
    .text(x_label);

    // Create Y axis label
    svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 0-margin.left)
    .attr("x", 0-margin.top)
    .attr("dy", "1em")
    .style("text-anchor", "end")
    .text(y_label);

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
    svg.append("g").attr("class", "x axis").attr("transform", "translate(0," + height + ")").call(xAxis);
    svg.append("g").attr("class", "y axis").call(yAxis)

}