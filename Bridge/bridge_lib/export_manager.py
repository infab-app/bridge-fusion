import logging
import traceback

import adsk.core
import adsk.fusion

logger = logging.getLogger("bridge")


class ExportManager:
    @staticmethod
    def _get_design():
        try:
            app = adsk.core.Application.get()
            design = adsk.fusion.Design.cast(app.activeProduct)
            if design:
                return design
            doc = app.activeDocument
            if doc:
                for i in range(doc.products.count):
                    product = doc.products.item(i)
                    design = adsk.fusion.Design.cast(product)
                    if design:
                        return design
            return None
        except Exception:
            return None

    @staticmethod
    def export_fusion_archive(filepath: str, component=None) -> bool:
        try:
            design = ExportManager._get_design()
            if not design:
                logger.error("Fusion Archive export failed: no Design product available")
                return False
            export_mgr = design.exportManager
            target = component or design.rootComponent
            options = export_mgr.createFusionArchiveExportOptions(filepath, target)
            result = export_mgr.execute(options)
            if result:
                logger.info(f"Exported F3D: {filepath}")
            else:
                logger.error(f"Fusion Archive export returned failure: {filepath}")
            return result
        except Exception:
            logger.error(f"Fusion Archive export failed: {traceback.format_exc()}")
            return False

    @staticmethod
    def export_step(filepath: str, component=None) -> bool:
        try:
            design = ExportManager._get_design()
            if not design:
                logger.error("STEP export failed: no Design product available")
                return False
            export_mgr = design.exportManager
            options = export_mgr.createSTEPExportOptions(
                filepath, component or design.rootComponent
            )
            result = export_mgr.execute(options)
            if result:
                logger.info(f"Exported STEP: {filepath}")
            else:
                logger.error(f"STEP export returned failure: {filepath}")
            return result
        except Exception:
            logger.error(f"STEP export failed: {traceback.format_exc()}")
            return False

    @staticmethod
    def export_stl(filepath: str, component=None) -> bool:
        try:
            design = ExportManager._get_design()
            if not design:
                logger.error("STL export failed: no Design product available")
                return False
            export_mgr = design.exportManager
            target = component or design.rootComponent
            options = export_mgr.createSTLExportOptions(target, filepath)
            result = export_mgr.execute(options)
            if result:
                logger.info(f"Exported STL: {filepath}")
            else:
                logger.error(f"STL export returned failure: {filepath}")
            return result
        except Exception:
            logger.error(f"STL export failed: {traceback.format_exc()}")
            return False

    @staticmethod
    def export_iges(filepath: str, component=None) -> bool:
        try:
            design = ExportManager._get_design()
            if not design:
                logger.error("IGES export failed: no Design product available")
                return False
            export_mgr = design.exportManager
            options = export_mgr.createIGESExportOptions(
                filepath, component or design.rootComponent
            )
            result = export_mgr.execute(options)
            if result:
                logger.info(f"Exported IGES: {filepath}")
            else:
                logger.error(f"IGES export returned failure: {filepath}")
            return result
        except Exception:
            logger.error(f"IGES export failed: {traceback.format_exc()}")
            return False

    @staticmethod
    def has_external_references() -> bool:
        try:
            design = ExportManager._get_design()
            if not design:
                return False
            return any(occ.isReferencedComponent for occ in design.rootComponent.allOccurrences)
        except Exception:
            return False

    @staticmethod
    def get_components():
        try:
            design = ExportManager._get_design()
            if not design:
                return []
            root = design.rootComponent
            components = [("Root Component", root)]
            for i in range(root.occurrences.count):
                occ = root.occurrences.item(i)
                components.append((occ.name, occ.component))
            return components
        except Exception:
            return []
