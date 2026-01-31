CoreRescue
CoreRescue is a specialized High Dynamic Range (HDR) stretching tool designed to prevent bright celestial cores from blowing out while revealing faint outer nebulosity. It works by performing two simultaneous stretches on linear data—a color-safe asinh stretch for highlights and an aggressive midtone stretch for the background—then seamlessly merges them using a blurred luminosity mask. This dual-path approach allows users to "rescue" details like the Trapezium stars in M42 while maintaining deep, high-contrast nebula dust.

StarRecombiner
StarRecombiner is a precision utility for blending starless images with linear star masks to create natural, aesthetically pleasing astronomical compositions. By utilizing a "Screen" blending algorithm within Siril’s PixelMath engine, the tool ensures stars are added back into the nebula without harsh artifacts or unnatural overlapping. It provides real-time control over star brightness, saturation, and soft Gaussian blurring, allowing for perfect integration between the stars and the deep-sky background.

Requirements
To run these tools, you need a standard installation of Siril (1.2.0 or newer). The scripts will automatically attempt to install the following dependencies into Siril's internal Python environment on first launch:

Python 3.10+: Included with the Siril installer.
pySiril: The official Python bridge for Siril command execution.
Pillow (PIL): Used for high-speed image preview rendering within the UI.
Tkinter: The standard Python GUI toolkit (usually pre-installed with Python).


Credits & Acknowledgments
These tools were developed to bridge the gap between complex mathematical processing and an intuitive user experience.

Lead Developer: Tony B. (TB)
AI Architecture & Optimization: Gemini (Google DeepMind)

Core Math & Logic: Based on Siril's powerful PixelMath and asinh implementation.
Special Thanks: * Cyril Richard and the Siril team for the pySiril library.
Franklin Marek (SetiAstro) for the inspiration behind HDR multi-scale techniques in astrophotography.

The Siril Community for their ongoing testing and feedback.

How to Install (Quick Guide)
READ THE USER GUIDES
Download the .py files.
Place them in your Siril scripts folder:

%AppData%\siril\scripts\ (Windows) or ~/.local/share/siril/scripts/ (Linux).

In Siril, go to Scripts ➔ Refresh Scripts.

Launch via Scripts ➔ Python Scripts.
