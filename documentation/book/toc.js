// Populate the sidebar
//
// This is a script, and not included directly in the page, to control the total size of the book.
// The TOC contains an entry for each page, so if each page includes a copy of the TOC,
// the total size of the page becomes O(n**2).
class MDBookSidebarScrollbox extends HTMLElement {
    constructor() {
        super();
    }
    connectedCallback() {
        this.innerHTML = '<ol class="chapter"><li class="chapter-item expanded affix "><a href="introduction.html">Introduction</a></li><li class="chapter-item expanded affix "><li class="spacer"></li><li class="chapter-item expanded affix "><li class="part-title">Getting Started</li><li class="chapter-item expanded "><a href="getting-started/installation.html"><strong aria-hidden="true">1.</strong> Installation</a></li><li class="chapter-item expanded "><a href="getting-started/quick-start.html"><strong aria-hidden="true">2.</strong> Quick Start</a></li><li class="chapter-item expanded affix "><li class="spacer"></li><li class="chapter-item expanded affix "><li class="part-title">Core Concepts</li><li class="chapter-item expanded "><a href="core/nodes.html"><strong aria-hidden="true">3.</strong> Nodes &amp; Node Manager</a></li><li class="chapter-item expanded "><a href="core/simulation-config.html"><strong aria-hidden="true">4.</strong> Simulation Configuration</a></li><li class="chapter-item expanded "><a href="core/circuit.html"><strong aria-hidden="true">5.</strong> Circuit</a></li><li class="chapter-item expanded affix "><li class="spacer"></li><li class="chapter-item expanded affix "><li class="part-title">Components</li><li class="chapter-item expanded "><a href="components/overview.html"><strong aria-hidden="true">6.</strong> Overview</a></li><li class="chapter-item expanded "><a href="components/passive.html"><strong aria-hidden="true">7.</strong> Passive Components</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="components/resistor.html"><strong aria-hidden="true">7.1.</strong> Resistor</a></li><li class="chapter-item expanded "><a href="components/capacitor.html"><strong aria-hidden="true">7.2.</strong> Capacitor</a></li><li class="chapter-item expanded "><a href="components/inductor.html"><strong aria-hidden="true">7.3.</strong> Inductor</a></li></ol></li><li class="chapter-item expanded "><a href="components/semiconductors.html"><strong aria-hidden="true">8.</strong> Semiconductor Components</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="components/diode.html"><strong aria-hidden="true">8.1.</strong> Diode</a></li><li class="chapter-item expanded "><a href="components/zener-diode.html"><strong aria-hidden="true">8.2.</strong> Zener Diode</a></li><li class="chapter-item expanded "><a href="components/bjt.html"><strong aria-hidden="true">8.3.</strong> BJT (Bipolar Junction Transistor)</a></li><li class="chapter-item expanded "><a href="components/mosfet.html"><strong aria-hidden="true">8.4.</strong> MOSFET</a></li></ol></li><li class="chapter-item expanded "><a href="components/ics.html"><strong aria-hidden="true">9.</strong> Integrated Circuits</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="components/opamp.html"><strong aria-hidden="true">9.1.</strong> Op-Amp</a></li></ol></li><li class="chapter-item expanded "><a href="components/magnetic.html"><strong aria-hidden="true">10.</strong> Magnetic Components</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="components/mutual-coupling.html"><strong aria-hidden="true">10.1.</strong> Mutual Coupling</a></li><li class="chapter-item expanded "><a href="components/transformer.html"><strong aria-hidden="true">10.2.</strong> Transformer</a></li></ol></li><li class="chapter-item expanded "><a href="components/sources.html"><strong aria-hidden="true">11.</strong> Sources</a></li><li><ol class="section"><li class="chapter-item expanded "><a href="components/voltage-source.html"><strong aria-hidden="true">11.1.</strong> Voltage Source &amp; Waveforms</a></li><li class="chapter-item expanded "><a href="components/dependent-sources.html"><strong aria-hidden="true">11.2.</strong> Dependent Sources (VCVS, VCCS, CCVS, CCCS)</a></li></ol></li><li class="chapter-item expanded "><li class="spacer"></li><li class="chapter-item expanded affix "><li class="part-title">Simulation</li><li class="chapter-item expanded "><a href="simulation/overview.html"><strong aria-hidden="true">12.</strong> How Simulation Works</a></li><li class="chapter-item expanded "><a href="simulation/mna.html"><strong aria-hidden="true">13.</strong> MNA Formulation</a></li><li class="chapter-item expanded "><a href="simulation/newton-raphson.html"><strong aria-hidden="true">14.</strong> Newton–Raphson Solver</a></li><li class="chapter-item expanded "><a href="simulation/dc-operating-point.html"><strong aria-hidden="true">15.</strong> DC Operating Point</a></li><li class="chapter-item expanded "><a href="simulation/transient.html"><strong aria-hidden="true">16.</strong> Transient Analysis</a></li><li class="chapter-item expanded "><a href="simulation/convergence.html"><strong aria-hidden="true">17.</strong> Convergence Helpers</a></li><li class="chapter-item expanded affix "><li class="spacer"></li><li class="chapter-item expanded affix "><li class="part-title">Visualization</li><li class="chapter-item expanded "><a href="visualization/probes.html"><strong aria-hidden="true">18.</strong> Probes</a></li><li class="chapter-item expanded "><a href="visualization/live-plotting.html"><strong aria-hidden="true">19.</strong> Live Plotting</a></li><li class="chapter-item expanded "><a href="visualization/live-simulation.html"><strong aria-hidden="true">20.</strong> Live Simulation</a></li><li class="chapter-item expanded affix "><li class="spacer"></li><li class="chapter-item expanded affix "><li class="part-title">Pre-Built Library</li><li class="chapter-item expanded "><a href="library/overview.html"><strong aria-hidden="true">21.</strong> Component Library</a></li><li class="chapter-item expanded "><a href="library/common.html"><strong aria-hidden="true">22.</strong> Common Building Blocks</a></li><li class="chapter-item expanded affix "><li class="spacer"></li><li class="chapter-item expanded affix "><li class="part-title">Examples</li><li class="chapter-item expanded "><a href="examples/half-wave-rectifier.html"><strong aria-hidden="true">23.</strong> Half-Wave Rectifier</a></li><li class="chapter-item expanded "><a href="examples/ce-amplifier.html"><strong aria-hidden="true">24.</strong> CE Amplifier</a></li><li class="chapter-item expanded "><a href="examples/zener-regulator.html"><strong aria-hidden="true">25.</strong> Zener Regulator</a></li><li class="chapter-item expanded "><a href="examples/linear-power-supply.html"><strong aria-hidden="true">26.</strong> Linear Power Supply</a></li><li class="chapter-item expanded "><a href="examples/lcr.html"><strong aria-hidden="true">27.</strong> Series LCR</a></li><li class="chapter-item expanded "><a href="examples/transformer.html"><strong aria-hidden="true">28.</strong> Transformer</a></li><li class="chapter-item expanded affix "><li class="spacer"></li><li class="chapter-item expanded affix "><li class="part-title">Extending PyEEL</li><li class="chapter-item expanded "><a href="extending/new-components.html"><strong aria-hidden="true">29.</strong> Adding New Components</a></li><li class="chapter-item expanded "><a href="extending/new-library-parts.html"><strong aria-hidden="true">30.</strong> Adding Library Parts</a></li></ol>';
        // Set the current, active page, and reveal it if it's hidden
        let current_page = document.location.href.toString();
        if (current_page.endsWith("/")) {
            current_page += "index.html";
        }
        var links = Array.prototype.slice.call(this.querySelectorAll("a"));
        var l = links.length;
        for (var i = 0; i < l; ++i) {
            var link = links[i];
            var href = link.getAttribute("href");
            if (href && !href.startsWith("#") && !/^(?:[a-z+]+:)?\/\//.test(href)) {
                link.href = path_to_root + href;
            }
            // The "index" page is supposed to alias the first chapter in the book.
            if (link.href === current_page || (i === 0 && path_to_root === "" && current_page.endsWith("/index.html"))) {
                link.classList.add("active");
                var parent = link.parentElement;
                if (parent && parent.classList.contains("chapter-item")) {
                    parent.classList.add("expanded");
                }
                while (parent) {
                    if (parent.tagName === "LI" && parent.previousElementSibling) {
                        if (parent.previousElementSibling.classList.contains("chapter-item")) {
                            parent.previousElementSibling.classList.add("expanded");
                        }
                    }
                    parent = parent.parentElement;
                }
            }
        }
        // Track and set sidebar scroll position
        this.addEventListener('click', function(e) {
            if (e.target.tagName === 'A') {
                sessionStorage.setItem('sidebar-scroll', this.scrollTop);
            }
        }, { passive: true });
        var sidebarScrollTop = sessionStorage.getItem('sidebar-scroll');
        sessionStorage.removeItem('sidebar-scroll');
        if (sidebarScrollTop) {
            // preserve sidebar scroll position when navigating via links within sidebar
            this.scrollTop = sidebarScrollTop;
        } else {
            // scroll sidebar to current active section when navigating via "next/previous chapter" buttons
            var activeSection = document.querySelector('#sidebar .active');
            if (activeSection) {
                activeSection.scrollIntoView({ block: 'center' });
            }
        }
        // Toggle buttons
        var sidebarAnchorToggles = document.querySelectorAll('#sidebar a.toggle');
        function toggleSection(ev) {
            ev.currentTarget.parentElement.classList.toggle('expanded');
        }
        Array.from(sidebarAnchorToggles).forEach(function (el) {
            el.addEventListener('click', toggleSection);
        });
    }
}
window.customElements.define("mdbook-sidebar-scrollbox", MDBookSidebarScrollbox);
