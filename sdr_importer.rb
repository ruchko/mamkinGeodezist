# -*- coding: utf-8 -*-
require 'sketchup.rb'

module KirillRuchko
  module SdrImporter

    def self.import_sdr
      path = UI.openpanel("Выберите SDR файл", "", "SDR Files|*.sdr;*.txt|All Files|*.*")
      return unless path

      model = Sketchup.active_model
      entities = model.active_entities
      
      # Массив для хранения объектов Point3d для последующего соединения линиями
      points_list = []
      point_count = 0
      
      # Так как в SDR точки в метрах, используем коэффициент 1.0
      unit_scale = 39.3700787401575

      model.start_operation("Импорт SDR с линиями", true)

      File.foreach(path, encoding: 'UTF-8') do |line|
        line = line.chomp
        next if line.length < 4

        rec_type = line[0, 2].strip
        name = nil
        north = nil
        east = nil
        elev = nil

        # Парсинг (логика прежняя, оптимизирована для типов 02, 08, 18)
        case rec_type
        when "02", "08", "18"
          if line.length >= 68 # SDR33
            name   = line[4, 16].strip
            north  = line[20, 16].to_f
            east   = line[36, 16].to_f
            elev   = line[52, 16].to_f
          elsif line.length >= 38 # SDR2x
            name   = line[4, 4].strip
            north  = line[8, 10].to_f
            east   = line[18, 10].to_f
            elev   = line[28, 10].to_f
          end
        end

        if name && north && east && elev
          # Координаты: East -> X, North -> Y, Elev -> Z
          pt = Geom::Point3d.new(east * unit_scale, north * unit_scale, elev * unit_scale)
          
          # Создаем точку
          entities.add_cpoint(pt)
          entities.add_text("#{name}", pt)
          
          # Соединяем с предыдущей точкой, если она существует
          unless points_list.empty?
            entities.add_line(points_list.last, pt)
          end
          
          points_list << pt
          point_count += 1
        end
      end

      model.commit_operation
      UI.messageBox("Импорт завершен! Создано точек: #{point_count}, линий: #{[0, point_count-1].max}")
    end

    unless file_loaded?(__FILE__)
      plugins_menu = UI.menu("Plugins")
      plugins_menu.add_item("Импортировать точки и линии из SDR...") {
        import_sdr
      }
      file_loaded(__FILE__)
    end

  end
end
