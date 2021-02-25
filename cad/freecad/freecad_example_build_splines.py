from FreeCAD import Base
import Part

doc = App.newDocument('mydoc')

# def main():

V = Base.Vector
poles = [V(-10, 0), V(0, -10), V(10, 0)]

# non-periodic spline
n = Part.BSplineCurve()
knots = (-2.5, -2, -1.5, -1, 0, 1)
mults = tuple([1] * len(knots))
n.buildFromPolesMultsKnots(poles, mults, knots, False, 2)
# obj1 = doc.addObject('Part::Feature', 'non_periodic_spline')
# obj1.Shape = n.toShape()
Part.show(n.toShape())

# periodic spline
p = Part.BSplineCurve()
p.buildFromPolesMultsKnots(poles, (1, 1, 1, 1, 1), (0, 0.25, 0.5, 0.75, 1), True, 2)
Part.show(p.toShape())
obj2 = doc.addObject('Part::Feature', 'periodic_spline')
obj2.Shape = p.toShape()

# # periodic and rational spline
# r = Part.BSplineCurve()
# r.buildFromPolesMultsKnots(poles, (1, 1, 1, 1, 1), (0, 0.25, 0.5, 0.75, 1), True, 2, (1, 0.8, 0.7, 0.2))
# Part.show(r.toShape())
# obj3 = doc.addObject('Part::Feature', 'periodic_rational_spline')
# obj3.Shape = r.toShape()

# main()
doc.saveAs('./splines1.FCStd')
