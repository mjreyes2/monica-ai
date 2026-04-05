"""
Test script to verify all AR/Holographic Teaching System libraries are working
Tests each library independently to ensure compatibility
"""

import sys
import traceback

def test_manim():
    """Test Manim animation engine"""
    try:
        from manim import Scene, Text, Write, FadeOut
        print("[OK] Manim: Successfully imported")
        return True
    except Exception as e:
        print(f"[X] Manim: Failed - {e}")
        traceback.print_exc()
        return False

def test_pyvista():
    """Test PyVista 3D visualization"""
    try:
        import pyvista as pv
        # Create simple mesh
        mesh = pv.Sphere(radius=1.0)
        print(f"[OK] PyVista: Successfully imported (created sphere with {mesh.n_points} points)")
        return True
    except Exception as e:
        print(f"[X] PyVista: Failed - {e}")
        traceback.print_exc()
        return False

def test_open3d():
    """Test Open3D advanced 3D"""
    try:
        import open3d as o3d
        # Create simple mesh
        mesh = o3d.geometry.TriangleMesh.create_sphere(radius=1.0)
        print(f"[OK] Open3D: Successfully imported (created sphere with {len(mesh.vertices)} vertices)")
        return True
    except Exception as e:
        print(f"[X] Open3D: Failed - {e}")
        traceback.print_exc()
        return False

def test_ursina():
    """Test Ursina game engine"""
    try:
        from ursina import Entity, Vec3
        print("[OK] Ursina: Successfully imported")
        return True
    except Exception as e:
        print(f"[X] Ursina: Failed - {e}")
        traceback.print_exc()
        return False

def test_opencv_aruco():
    """Test OpenCV ArUco markers (already in Monica)"""
    try:
        import cv2
        import cv2.aruco as aruco
        # Get ArUco dictionary
        aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
        print(f"[OK] OpenCV ArUco: Successfully imported (dictionary loaded)")
        return True
    except Exception as e:
        print(f"[X] OpenCV ArUco: Failed - {e}")
        traceback.print_exc()
        return False

def test_pygame():
    """Test Pygame for sound effects"""
    try:
        import pygame
        pygame.mixer.init()
        print("[OK] Pygame: Successfully imported (mixer initialized)")
        pygame.mixer.quit()
        return True
    except Exception as e:
        print(f"[X] Pygame: Failed - {e}")
        traceback.print_exc()
        return False

def test_trimesh():
    """Test Trimesh for 3D mesh processing"""
    try:
        import trimesh
        # Create simple mesh
        mesh = trimesh.creation.box()
        print(f"[OK] Trimesh: Successfully imported (created box with {len(mesh.vertices)} vertices)")
        return True
    except Exception as e:
        print(f"[X] Trimesh: Failed - {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 70)
    print("AR/HOLOGRAPHIC TEACHING SYSTEM - LIBRARY COMPATIBILITY TEST")
    print("=" * 70)
    print()
    
    tests = [
        ("Manim (Animation Engine)", test_manim),
        ("PyVista (3D Visualization)", test_pyvista),
        ("Open3D (Advanced 3D)", test_open3d),
        ("Ursina (Game Engine)", test_ursina),
        ("OpenCV ArUco (AR Markers)", test_opencv_aruco),
        ("Pygame (Sound Effects)", test_pygame),
        ("Trimesh (3D Mesh Processing)", test_trimesh),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\nTesting {name}...")
        result = test_func()
        results.append((name, result))
    
    print()
    print("=" * 70)
    print("TEST RESULTS SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK] PASS" if result else "[X] FAIL"
        print(f"{status}: {name}")
    
    print()
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print()
    
    if passed == total:
        print("[PARTY] ALL TESTS PASSED! AR/Holographic Teaching System is ready!")
    else:
        print("[WARN] Some tests failed. Check errors above.")
    
    print("=" * 70)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
