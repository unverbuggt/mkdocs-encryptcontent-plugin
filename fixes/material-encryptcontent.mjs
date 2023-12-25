//tested with mkdocs-material 9.5.2

import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';

function material_mermaid_init() {
  //this is taken straight from the compiled typescript bundle of mkdocs-material
  let themeCSS=".node circle,.node ellipse,.node path,.node polygon,.node rect{fill:var(--md-mermaid-node-bg-color);stroke:var(--md-mermaid-node-fg-color)}marker{fill:var(--md-mermaid-edge-color)!important}.edgeLabel .label rect{fill:#0000}.label{color:var(--md-mermaid-label-fg-color);font-family:var(--md-mermaid-font-family)}.label foreignObject{line-height:normal;overflow:visible}.label div .edgeLabel{color:var(--md-mermaid-label-fg-color)}.edgeLabel,.edgeLabel rect,.label div .edgeLabel{background-color:var(--md-mermaid-label-bg-color)}.edgeLabel,.edgeLabel rect{fill:var(--md-mermaid-label-bg-color);color:var(--md-mermaid-edge-color)}.edgePath .path,.flowchart-link{stroke:var(--md-mermaid-edge-color);stroke-width:.05rem}.edgePath .arrowheadPath{fill:var(--md-mermaid-edge-color);stroke:none}.cluster rect{fill:var(--md-default-fg-color--lightest);stroke:var(--md-default-fg-color--lighter)}.cluster span{color:var(--md-mermaid-label-fg-color);font-family:var(--md-mermaid-font-family)}g #flowchart-circleEnd,g #flowchart-circleStart,g #flowchart-crossEnd,g #flowchart-crossStart,g #flowchart-pointEnd,g #flowchart-pointStart{stroke:none}g.classGroup line,g.classGroup rect{fill:var(--md-mermaid-node-bg-color);stroke:var(--md-mermaid-node-fg-color)}g.classGroup text{fill:var(--md-mermaid-label-fg-color);font-family:var(--md-mermaid-font-family)}.classLabel .box{fill:var(--md-mermaid-label-bg-color);background-color:var(--md-mermaid-label-bg-color);opacity:1}.classLabel .label{fill:var(--md-mermaid-label-fg-color);font-family:var(--md-mermaid-font-family)}.node .divider{stroke:var(--md-mermaid-node-fg-color)}.relation{stroke:var(--md-mermaid-edge-color)}.cardinality{fill:var(--md-mermaid-label-fg-color);font-family:var(--md-mermaid-font-family)}.cardinality text{fill:inherit!important}defs #classDiagram-compositionEnd,defs #classDiagram-compositionStart,defs #classDiagram-dependencyEnd,defs #classDiagram-dependencyStart,defs #classDiagram-extensionEnd,defs #classDiagram-extensionStart{fill:var(--md-mermaid-edge-color)!important;stroke:var(--md-mermaid-edge-color)!important}defs #classDiagram-aggregationEnd,defs #classDiagram-aggregationStart{fill:var(--md-mermaid-label-bg-color)!important;stroke:var(--md-mermaid-edge-color)!important}g.stateGroup rect{fill:var(--md-mermaid-node-bg-color);stroke:var(--md-mermaid-node-fg-color)}g.stateGroup .state-title{fill:var(--md-mermaid-label-fg-color)!important;font-family:var(--md-mermaid-font-family)}g.stateGroup .composit{fill:var(--md-mermaid-label-bg-color)}.nodeLabel{color:var(--md-mermaid-label-fg-color);font-family:var(--md-mermaid-font-family)}.node circle.state-end,.node circle.state-start,.start-state{fill:var(--md-mermaid-edge-color);stroke:none}.end-state-inner,.end-state-outer{fill:var(--md-mermaid-edge-color)}.end-state-inner,.node circle.state-end{stroke:var(--md-mermaid-label-bg-color)}.transition{stroke:var(--md-mermaid-edge-color)}[id^=state-fork] rect,[id^=state-join] rect{fill:var(--md-mermaid-edge-color)!important;stroke:none!important}.statediagram-cluster.statediagram-cluster .inner{fill:var(--md-default-bg-color)}.statediagram-cluster rect{fill:var(--md-mermaid-node-bg-color);stroke:var(--md-mermaid-node-fg-color)}.statediagram-state rect.divider{fill:var(--md-default-fg-color--lightest);stroke:var(--md-default-fg-color--lighter)}defs #statediagram-barbEnd{stroke:var(--md-mermaid-edge-color)}.attributeBoxEven,.attributeBoxOdd{fill:var(--md-mermaid-node-bg-color);stroke:var(--md-mermaid-node-fg-color)}.entityBox{fill:var(--md-mermaid-label-bg-color);stroke:var(--md-mermaid-node-fg-color)}.entityLabel{fill:var(--md-mermaid-label-fg-color);font-family:var(--md-mermaid-font-family)}.relationshipLabelBox{fill:var(--md-mermaid-label-bg-color);fill-opacity:1;background-color:var(--md-mermaid-label-bg-color);opacity:1}.relationshipLabel{fill:var(--md-mermaid-label-fg-color)}.relationshipLine{stroke:var(--md-mermaid-edge-color)}defs #ONE_OR_MORE_END *,defs #ONE_OR_MORE_START *,defs #ONLY_ONE_END *,defs #ONLY_ONE_START *,defs #ZERO_OR_MORE_END *,defs #ZERO_OR_MORE_START *,defs #ZERO_OR_ONE_END *,defs #ZERO_OR_ONE_START *{stroke:var(--md-mermaid-edge-color)!important}defs #ZERO_OR_MORE_END circle,defs #ZERO_OR_MORE_START circle{fill:var(--md-mermaid-label-bg-color)}.actor{fill:var(--md-mermaid-sequence-actor-bg-color);stroke:var(--md-mermaid-sequence-actor-border-color)}text.actor>tspan{fill:var(--md-mermaid-sequence-actor-fg-color);font-family:var(--md-mermaid-font-family)}line{stroke:var(--md-mermaid-sequence-actor-line-color)}.actor-man circle,.actor-man line{fill:var(--md-mermaid-sequence-actorman-bg-color);stroke:var(--md-mermaid-sequence-actorman-line-color)}.messageLine0,.messageLine1{stroke:var(--md-mermaid-sequence-message-line-color)}.note{fill:var(--md-mermaid-sequence-note-bg-color);stroke:var(--md-mermaid-sequence-note-border-color)}.loopText,.loopText>tspan,.messageText,.noteText>tspan{stroke:none;font-family:var(--md-mermaid-font-family)!important}.messageText{fill:var(--md-mermaid-sequence-message-fg-color)}.loopText,.loopText>tspan{fill:var(--md-mermaid-sequence-loop-fg-color)}.noteText>tspan{fill:var(--md-mermaid-sequence-note-fg-color)}#arrowhead path{fill:var(--md-mermaid-sequence-message-line-color);stroke:none}.loopLine{fill:var(--md-mermaid-sequence-loop-bg-color);stroke:var(--md-mermaid-sequence-loop-border-color)}.labelBox{fill:var(--md-mermaid-sequence-label-bg-color);stroke:none}.labelText,.labelText>span{fill:var(--md-mermaid-sequence-label-fg-color);font-family:var(--md-mermaid-font-family)}.sequenceNumber{fill:var(--md-mermaid-sequence-number-fg-color)}rect.rect{fill:var(--md-mermaid-sequence-box-bg-color);stroke:none}rect.rect+text.text{fill:var(--md-mermaid-sequence-box-fg-color)}defs #sequencenumber{fill:var(--md-mermaid-sequence-number-bg-color)!important}";

  mermaid.initialize({
    startOnLoad: false,
    themeCSS:themeCSS,
    sequence:{
      actorFontSize:"16px",
      messageFontSize:"16px",
      noteFontSize:"16px"
    }
  });
}

async function material_mermaid_run() {
  const graphs = document.querySelectorAll("pre.mermaid");
  let id;
  for (let i = 0; i < graphs.length; i++) {
    id = '__mermaid_'+i
    graphs[i].classList.remove("mermaid")
    let graph = document.createElement('div');
    graph.classList.add("mermaid");
    const { svg } = await mermaid.render(id, graphs[i].childNodes[0].innerText);
    const shadow = graph.attachShadow({ mode: "closed" })
    shadow.innerHTML = svg
    graphs[i].replaceWith(graph)
  }
};

//this function is run by mkdocs-encryptcontent-plugin after successfull decryption
function theme_run_after_decryption() {
    material_mermaid_init();
    material_mermaid_run();
}

window["theme_run_after_decryption"] = theme_run_after_decryption;