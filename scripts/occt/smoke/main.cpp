#include <BRepAlgoAPI_Cut.hxx>
#include <BRepBndLib.hxx>
#include <BRepCheck_Analyzer.hxx>
#include <BRepGProp.hxx>
#include <BRepMesh_IncrementalMesh.hxx>
#include <BRepPrimAPI_MakeBox.hxx>
#include <Bnd_Box.hxx>
#include <GProp_GProps.hxx>
#include <IGESControl_Writer.hxx>
#include <STEPControl_Reader.hxx>
#include <STEPControl_Writer.hxx>
#include <StlAPI_Writer.hxx>
#include <Standard_Version.hxx>
#include <dlfcn.h>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <string>
#ifdef __APPLE__
#include <mach-o/dyld.h>
#else
#include <link.h>
#endif

void record_library(const char* path) {
  if (path && std::string(path).find("/libTK") != std::string::npos)
    std::cout << "OCCT_LOADED_LIBRARY " << path << '\n';
}

void record_loaded_libraries() {
#ifdef __APPLE__
  for (uint32_t i = 0; i < _dyld_image_count(); ++i)
    record_library(_dyld_get_image_name(i));
#else
  dl_iterate_phdr([](dl_phdr_info* image, size_t, void*) {
    record_library(image->dlpi_name);
    return 0;
  }, nullptr);
#endif
}

void require(bool result, const char* message) {
  if (!result) throw std::runtime_error(message);
}

int main(int argc, char** argv) {
  try {
    require(argc > 1, "pass every installed toolkit path to verify loadability");
    for (int i = 1; i < argc; ++i) {
      void* handle = dlopen(argv[i], RTLD_NOW | RTLD_LOCAL);
      if (!handle) throw std::runtime_error(dlerror());
      // OCCT registers toolkit-owned factories globally. Keep toolkits loaded
      // for the consumer's lifetime, as a normal linked application does.
    }
    require(std::string(OCC_VERSION_COMPLETE) == "8.0.1", "wrong OCCT version");
    auto box = BRepPrimAPI_MakeBox(10., 20., 30.).Shape();
    require(BRepCheck_Analyzer(box).IsValid(), "invalid box");
    BRepAlgoAPI_Cut cut(box, BRepPrimAPI_MakeBox(5., 10., 30.).Shape());
    cut.Build();
    require(cut.IsDone() && BRepCheck_Analyzer(cut.Shape()).IsValid(), "Boolean failed");
    GProp_GProps props;
    BRepGProp::VolumeProperties(cut.Shape(), props);
    require(std::abs(props.Mass() - 4500.) < 1.e-6, "wrong Boolean volume");
    BRepMesh_IncrementalMesh mesh(cut.Shape(), 0.5);
    require(mesh.IsDone(), "meshing failed");
    STEPControl_Writer writer;
    require(writer.Transfer(cut.Shape(), STEPControl_AsIs) == IFSelect_RetDone, "STEP transfer");
    require(writer.Write("roundtrip.step") == IFSelect_RetDone, "STEP export");
    STEPControl_Reader reader;
    require(reader.ReadFile("roundtrip.step") == IFSelect_RetDone, "STEP import");
    require(reader.TransferRoots() > 0, "STEP roots");
    require(BRepCheck_Analyzer(reader.OneShape()).IsValid(), "STEP invalid shape");
    BRepGProp::VolumeProperties(reader.OneShape(), props);
    require(std::abs(props.Mass() - 4500.) < 1.e-5, "STEP changed volume");
    IGESControl_Writer iges("MM", 0);
    require(iges.AddShape(box) && iges.Write("box.iges"), "IGES export");
    StlAPI_Writer stl;
    BRepMesh_IncrementalMesh boxMesh(box, 0.5);
    require(stl.Write(box, "box.stl"), "STL export");
    record_loaded_libraries();
    std::cout << "OCCT 8.0.1: all toolkits load; BREP, Boolean, mesh, STEP, IGES, STL PASS\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
}
